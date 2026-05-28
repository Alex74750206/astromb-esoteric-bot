import re
import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import database as db
from config import PRODUCTS, ADMIN_IDS
from keyboards.inline import catalog_kb, product_kb
from texts.messages import CATALOG_HEADER
from utils.delivery import deliver_reading

router = Router()

DATE_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$")
TIME_RE = re.compile(r"^(\d{1,2})[:\.](\d{2})$")


class BuyFlow(StatesGroup):
    waiting_birth_date = State()
    waiting_name       = State()
    waiting_year       = State()
    waiting_time       = State()
    waiting_city       = State()


# ── Каталог ───────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "catalog")
async def cb_catalog(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer(CATALOG_HEADER, reply_markup=catalog_kb())
    await call.answer()


@router.callback_query(F.data.startswith("product:"))
async def cb_product_detail(call: CallbackQuery):
    product_id = call.data.split(":")[1]
    if product_id not in PRODUCTS:
        await call.answer("Продукт не найден", show_alert=True)
        return

    product = PRODUCTS[product_id]
    already = await db.has_purchased(call.from_user.id, product_id)

    text = (
        f"{product['name']}\n\n"
        f"{product['description']}\n\n"
        f"💫 Стоимость: <b>{product['price_stars']} ⭐ Telegram Stars</b>\n"
        f"⚡ Разбор приходит мгновенно в этот чат после оплаты"
    )
    await call.message.answer(text, reply_markup=product_kb(product_id, already))
    await call.answer()


# ── Начало покупки ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("buy:"))
async def cb_buy_start(call: CallbackQuery, state: FSMContext):
    product_id = call.data.split(":")[1]
    if product_id not in PRODUCTS:
        await call.answer("Продукт не найден", show_alert=True)
        return

    await state.update_data(product_id=product_id)
    await call.answer()

    user = await db.get_user(call.from_user.id)
    # Администратор всегда вводит данные заново (может проверять других людей)
    is_admin = call.from_user.id in ADMIN_IDS
    birth_date = (user.get("birth_date") if user else None) if not is_admin else None

    if birth_date:
        await state.update_data(birth_date=birth_date)
        await _next_step_after_date(call.message, state, product_id, user)
    else:
        prompt = (
            "👤 <b>Для кого делаем разбор?</b> Введи дату рождения:\n\n"
            if is_admin else
            "📅 Введи свою <b>дату рождения</b>:\n\n"
        )
        await call.message.answer(
            prompt + "<code>ДД.ММ.ГГГГ</code>  —  например: <code>15.03.1990</code>"
        )
        await state.set_state(BuyFlow.waiting_birth_date)


@router.message(BuyFlow.waiting_birth_date)
async def buy_birth_date(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    m = DATE_RE.match(text)
    if not m:
        await message.answer("⚠️ Формат: <code>ДД.ММ.ГГГГ</code>  например: <code>15.03.1990</code>")
        return

    day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2015):
        await message.answer("⚠️ Неверная дата. Проверь и введи снова: <code>ДД.ММ.ГГГГ</code>")
        return

    birth_date = f"{day:02d}.{month:02d}.{year:04d}"
    if message.from_user.id not in ADMIN_IDS:
        await db.update_user(message.from_user.id, birth_date=birth_date)
    await state.update_data(birth_date=birth_date)

    data = await state.get_data()
    user = await db.get_user(message.from_user.id)
    await _next_step_after_date(message, state, data["product_id"], user)


async def _next_step_after_date(msg, state: FSMContext, product_id: str, user: dict | None):
    product = PRODUCTS[product_id]
    is_admin = state.key.user_id in ADMIN_IDS

    if product.get("needs_name"):
        saved = (user.get("user_name_esoteric") if user else None) if not is_admin else None
        if saved:
            await state.update_data(user_name=saved)
            await _ask_year(msg, state)
        else:
            prompt = (
                "✍️ Введи <b>имя и фамилию</b> человека:\n\nНапример: <code>Мария Иванова</code>"
                if is_admin else
                "✍️ Введи своё <b>полное имя</b> (имя и фамилия):\n\nНапример: <code>Мария Иванова</code>"
            )
            await msg.answer(prompt)
            await state.set_state(BuyFlow.waiting_name)
    else:
        await _ask_year(msg, state)


@router.message(BuyFlow.waiting_name)
async def buy_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("⚠️ Введи настоящее имя (хотя бы 2 символа)")
        return
    if message.from_user.id not in ADMIN_IDS:
        await db.update_user(message.from_user.id, user_name_esoteric=name)
    await state.update_data(user_name=name)
    await _next_step_after_name(message, state)


async def _next_step_after_name(msg, state: FSMContext):
    await _ask_year(msg, state)


async def _ask_year(msg, state: FSMContext):
    next_year = datetime.datetime.now().year + 1
    await msg.answer(
        f"🗓 <b>На какой год сделать прогноз?</b>\n\n"
        f"Введите год, например: <code>{next_year}</code>"
    )
    await state.set_state(BuyFlow.waiting_year)


@router.message(BuyFlow.waiting_year)
async def buy_year(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    try:
        yr = int(text)
        if not (2020 <= yr <= 2040):
            raise ValueError
    except ValueError:
        await message.answer(
            "⚠️ Введите корректный год, например: <code>2026</code> или <code>2027</code>"
        )
        return
    await state.update_data(forecast_year=yr)
    await _next_step_after_year(message, state)


async def _next_step_after_year(msg, state: FSMContext):
    data = await state.get_data()
    product = PRODUCTS[data["product_id"]]
    if product.get("needs_time"):
        await msg.answer(
            "🕐 Введи <b>время рождения</b> (часы:минуты):\n\n"
            "Например: <code>14:30</code>\n\n"
            "Если не знаешь точное время — введи <code>12:00</code>"
        )
        await state.set_state(BuyFlow.waiting_time)
    else:
        await _send_invoice(msg, state)


@router.message(BuyFlow.waiting_time)
async def buy_time(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    m = TIME_RE.match(text)
    if not m:
        await message.answer(
            "⚠️ Формат времени: <code>ЧЧ:ММ</code>  например: <code>14:30</code>"
        )
        return

    hour, minute = int(m.group(1)), int(m.group(2))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        await message.answer("⚠️ Неверное время. Введи в формате <code>14:30</code>")
        return

    birth_time = f"{hour:02d}:{minute:02d}"
    await state.update_data(birth_time=birth_time)

    data = await state.get_data()
    if PRODUCTS[data["product_id"]].get("needs_city"):
        await message.answer(
            "📍 Введи <b>город рождения</b>:\n\n"
            "Например: <code>Москва</code>  или  <code>Алматы</code>"
        )
        await state.set_state(BuyFlow.waiting_city)
    else:
        await _send_invoice(message, state)


@router.message(BuyFlow.waiting_city)
async def buy_city(message: Message, state: FSMContext):
    city = (message.text or "").strip()
    if len(city) < 2:
        await message.answer("⚠️ Введи название города")
        return
    await state.update_data(birth_city=city)
    await _send_invoice(message, state)


# ── Финальная доставка или счёт ───────────────────────────────────────────────

async def _send_invoice(msg, state: FSMContext):
    data = await state.get_data()
    product_id   = data["product_id"]
    birth_date   = data.get("birth_date", "")
    name         = data.get("user_name", "")
    birth_time   = data.get("birth_time", "")
    birth_city   = data.get("birth_city", "")
    forecast_year = data.get("forecast_year", 2026)
    user_id      = state.key.user_id

    await state.clear()

    # Админ получает разбор бесплатно
    if user_id in ADMIN_IDS:
        await msg.answer(f"✅ <b>Доступ администратора — разбор бесплатно</b>\n📅 Год прогноза: {forecast_year}")
        await deliver_reading(msg, product_id, birth_date, name, birth_time, birth_city, year=forecast_year)
        return

    # Обычный пользователь — выставляем счёт
    from aiogram.types import LabeledPrice
    product = PRODUCTS[product_id]
    payload = f"{product_id}|{birth_time}|{birth_city}|{forecast_year}"

    await msg.answer_invoice(
        title=product["short_name"],
        description=product["description"][:255],
        payload=payload,
        currency="XTR",
        prices=[LabeledPrice(label=product["short_name"], amount=product["price_stars"])],
    )
