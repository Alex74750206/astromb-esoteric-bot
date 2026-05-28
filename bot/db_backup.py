"""Бэкап и восстановление БД в/из JSON для работы в CI/CD."""
import sqlite3, json, os

DB_PATH = os.getenv('DB_PATH', 'esoteric_bot.db')
BACKUP_PATH = 'db_backup.json'


def backup():
    if not os.path.exists(DB_PATH):
        print('DB not found, skip backup')
        return
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    data = {}
    for table in ['users', 'purchases']:
        try:
            rows = conn.execute(f'SELECT * FROM {table}').fetchall()
            data[table] = [dict(r) for r in rows]
        except Exception as e:
            data[table] = []
            print(f'Backup {table}: {e}')
    conn.close()
    with open(BACKUP_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    total = sum(len(v) for v in data.values())
    print(f'Backup: {total} records -> {BACKUP_PATH}')


def restore():
    if not os.path.exists(BACKUP_PATH):
        print('No backup found, starting fresh')
        return
    with open(BACKUP_PATH, encoding='utf-8') as f:
        data = json.load(f)
    conn = sqlite3.connect(DB_PATH)
    for table, rows in data.items():
        if not rows:
            continue
        cols = list(rows[0].keys())
        placeholders = ','.join(['?'] * len(cols))
        cols_str = ','.join(cols)
        for row in rows:
            try:
                conn.execute(
                    f'INSERT OR IGNORE INTO {table} ({cols_str}) VALUES ({placeholders})',
                    [row[c] for c in cols]
                )
            except Exception as e:
                print(f'Row skip ({table}): {e}')
    conn.commit()
    conn.close()
    total = sum(len(v) for v in data.values())
    print(f'Restore: {total} records from {BACKUP_PATH}')


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'backup':
        backup()
    else:
        restore()
