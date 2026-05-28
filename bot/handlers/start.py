import re
import os
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, FSInputFile

import database as db
from keyboards.inline import welcome_kb, after_free_reading_kb, catalog_kb
from keyboards.reply import main_kb
from texts.messages import WELCOME, ASK_BIRTH_DATE, WRONG_DATE_FORMAT, CATALOG_HEADER
from utils.numerology import free_reading_text

_BANNER = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "assets", "welcome_banner.jpg")
)

router = Router()

DATE_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$")


class LeadMagnet(StatesGroup):
    waiting_birth_date = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await db.add_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.full_name or "",
    )
    # Постоянная клавиатура внизу
    await message.answer("🌙 Меню доступно внизу 👇", reply_markup=main_kb())
    # Приветственный баннер
    if os.path.exists(_BANNER):
        await message.answer_photo(
            photo=FSInputFile(_BANNER),
            caption=(
                "🔮 <b>Ваш персональный астролог</b>\n\n"
                "Нумерология · Матрица судьбы · Натальная карта · Ба Цзы · Гороскоп 2026\n\n"
                "Все разборы — по вашей дате рождения, мгновенно в этот чат."
            ),
        )
    # Текст приветствия с кнопками
    await message.answer(WELCOME, reply_markup=welcome_kb())


@router.message(Command("catalog"))
@router.message(F.text == "🔮 Каталог")
async def cmd_catalog(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(CATALOG_HEADER, reply_markup=catalog_kb())


@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message):
    await message.answer(
        "🌙 <b>Что умеет этот бот:</b>\n\n"
        "✨ /start — Начать и получить бесплатный разбор\n"
        "🔮 /catalog — Каталог персональных разборов\n\n"
        "<b>Доступные разборы:</b>\n"
        "🔢 Нумерология — 15 ⭐\n"
        "🌟 Матрица судьбы — 20 ⭐\n"
        "♈ Гороскоп 2026 — 50 ⭐\n"
        "☯️ Ба Цзы — 50 ⭐\n"
        "🌌 Натальная карта — 100 ⭐\n\n"
        "Оплата — Telegram Stars, разбор приходит мгновенно в этот чат."
    )


# ── Бесплатный разбор ─────────────────────────────────────────────────────────

@router.message(F.text == "✨ Бесплатный разбор")
@router.callback_query(F.data == "lead_magnet")
async def start_lead_magnet(event, state: FSMContext):
    await state.clear()
    msg = event.message if isinstance(event, CallbackQuery) else event
    if isinstance(event, CallbackQuery):
        await event.message.edit_reply_markup(reply_markup=None)
        await event.answer()
    await msg.answer(ASK_BIRTH_DATE)
    await state.set_state(LeadMagnet.waiting_birth_date)


@router.message(LeadMagnet.waiting_birth_date)
async def process_lead_birth_date(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    m = DATE_RE.match(text)
    if not m:
        await message.answer(WRONG_DATE_FORMAT)
        return

    day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2015):
        await message.answer(WRONG_DATE_FORMAT)
        return

    birth_date = f"{day:02d}.{month:02d}.{year:04d}"
    await db.update_user(message.from_user.id, birth_date=birth_date)

    reading = free_reading_text(birth_date)
    await message.answer(reading)
    await message.answer(
        "🔮 Это лишь начало. Полные разборы с прогнозом по месяцам — в каталоге:",
        reply_markup=after_free_reading_kb(),
    )
    await state.clear()
