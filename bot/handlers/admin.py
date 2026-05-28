from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, FSInputFile
import os

import database as db
from config import ADMIN_IDS
from utils.excel_export import update_clients_excel, EXCEL_PATH

router = Router()


@router.message(Command("myid"))
async def cmd_myid(message: Message):
    """Любой пользователь может узнать свой Telegram ID."""
    await message.answer(
        f"🆔 Ваш Telegram ID: <code>{message.from_user.id}</code>\n\n"
        "Скопируйте это число — оно нужно для настройки бота как администратора."
    )


class BroadcastState(StatesGroup):
    waiting_message = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return

    stats = await db.get_stats()
    product_lines = "\n".join(
        f"  • {pid}: {cnt} шт. / {stars} ⭐"
        for pid, cnt, stars in stats["product_stats"]
    ) or "  нет покупок"

    await message.answer(
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Пользователей: <b>{stats['total_users']}</b>\n"
        f"💰 Покупок: <b>{stats['total_purchases']}</b>\n"
        f"⭐ Заработано Stars: <b>{stats['total_stars']}</b>\n\n"
        f"По продуктам:\n{product_lines}"
    )


@router.message(Command("excel"))
async def cmd_excel(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🔄 Обновляю Клиенты.xlsx...")
    count = await update_clients_excel()
    await message.answer(f"✅ Готово. Записей: {count}")


@router.message(Command("getfile"))
async def cmd_getfile(message: Message):
    if not is_admin(message.from_user.id):
        return
    count = await update_clients_excel()
    if not os.path.exists(EXCEL_PATH):
        await message.answer("❌ Файл не найден.")
        return
    await message.answer_document(
        FSInputFile(EXCEL_PATH, filename="Клиенты.xlsx"),
        caption=f"📊 База клиентов — {count} записей",
    )


@router.message(Command("broadcast"))
async def cmd_broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "📢 Введи текст рассылки.\n\n"
        "Поддерживается HTML-форматирование. "
        "Отправь /cancel для отмены."
    )
    await state.set_state(BroadcastState.waiting_message)


@router.message(Command("cancel"), BroadcastState.waiting_message)
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Рассылка отменена.")


@router.message(BroadcastState.waiting_message)
async def process_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    user_ids = await db.get_all_user_ids()

    sent, failed = 0, 0
    for uid in user_ids:
        try:
            await message.bot.send_message(uid, message.text or message.caption or "")
            sent += 1
        except Exception:
            failed += 1

    await message.answer(
        f"📢 Рассылка завершена:\n"
        f"✅ Отправлено: {sent}\n"
        f"❌ Ошибок: {failed}"
    )
