from __future__ import annotations
import aiosqlite
from config import DB_PATH
from utils.excel_export import update_clients_excel


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                birth_date TEXT,
                user_name_esoteric TEXT,
                funnel_step INTEGER DEFAULT 0,
                funnel_started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id TEXT,
                stars_paid INTEGER,
                charge_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        await db.commit()


async def add_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username, full_name),
        )
        await db.commit()
    await update_clients_excel()


async def get_user(user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def update_user(user_id: int, **kwargs):
    if not kwargs:
        return
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [user_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE users SET {sets} WHERE user_id = ?", values)
        await db.commit()
    if "birth_date" in kwargs or "username" in kwargs or "full_name" in kwargs:
        await update_clients_excel()


async def has_purchased(user_id: int, product_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id FROM purchases WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        ) as cur:
            return await cur.fetchone() is not None


async def add_purchase(user_id: int, product_id: str, stars_paid: int, charge_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO purchases (user_id, product_id, stars_paid, charge_id) VALUES (?, ?, ?, ?)",
            (user_id, product_id, stars_paid, charge_id),
        )
        await db.commit()
    await update_clients_excel()


async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total_users = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM purchases") as cur:
            total_purchases = (await cur.fetchone())[0]
        async with db.execute("SELECT COALESCE(SUM(stars_paid), 0) FROM purchases") as cur:
            total_stars = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT product_id, COUNT(*) as cnt, SUM(stars_paid) as stars FROM purchases GROUP BY product_id"
        ) as cur:
            product_stats = await cur.fetchall()
    return {
        "total_users": total_users,
        "total_purchases": total_purchases,
        "total_stars": total_stars,
        "product_stats": product_stats,
    }


async def get_all_user_ids() -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            return [r[0] for r in await cur.fetchall()]


async def get_users_for_funnel_step(step: int, min_hours: int) -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT user_id FROM users
               WHERE funnel_step = ?
               AND datetime(funnel_started_at, '+' || ? || ' hours') <= datetime('now')""",
            (step, min_hours),
        ) as cur:
            return [r[0] for r in await cur.fetchall()]
