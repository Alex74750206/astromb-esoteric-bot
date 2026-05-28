import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

import database as db
from texts.funnel import FUNNEL_STEPS
from keyboards.inline import to_catalog_kb

log = logging.getLogger(__name__)


async def send_funnel_messages(bot: Bot):
    """Проверяем воронку каждый час и отправляем нужные сообщения."""
    for step, (min_hours, text) in FUNNEL_STEPS.items():
        user_ids = await db.get_users_for_funnel_step(step - 1, min_hours)
        for uid in user_ids:
            try:
                if step == len(FUNNEL_STEPS):
                    await bot.send_message(uid, text, reply_markup=to_catalog_kb())
                else:
                    await bot.send_message(uid, text)
                await db.update_user(uid, funnel_step=step)
            except Exception as e:
                log.warning("Funnel send failed for %s: %s", uid, e)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_funnel_messages,
        trigger="interval",
        hours=1,
        args=[bot],
        id="funnel",
    )
    return scheduler
