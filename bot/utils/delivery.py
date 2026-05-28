"""Общая функция выдачи разбора — используется и для admin (бесплатно), и после оплаты."""
from aiogram.types import Message

from config import PRODUCTS
from keyboards.inline import to_catalog_kb
from utils.numerology import numerology_full_text, matrix_full_text, horoscope_full_text
from utils.bazi import bazi_full_text
from utils.natal import natal_full_text

MAX_LEN = 4000


async def deliver_reading(
    message: Message,
    product_id: str,
    birth_date: str,
    name: str = "",
    birth_time: str = "12:00",
    birth_city: str = "",
    year: int = 2026,
):
    if product_id == "numerology":
        text = numerology_full_text(birth_date, name or message.from_user.full_name or "Клиент", year)
    elif product_id == "matrix":
        text = matrix_full_text(birth_date, year)
    elif product_id == "horoscope":
        text = horoscope_full_text(birth_date, year)
    elif product_id == "bazi":
        text = bazi_full_text(birth_date, year)
    elif product_id == "natal":
        text = natal_full_text(birth_date, birth_time or "12:00", birth_city or "не указан", year)
    else:
        await message.answer("⚠️ Неизвестный продукт.")
        return

    if len(text) <= MAX_LEN:
        await message.answer(text)
    else:
        for i in range(0, len(text), MAX_LEN):
            await message.answer(text[i : i + MAX_LEN])

    product = PRODUCTS.get(product_id, {})
    await message.answer(
        f"✅ <b>{product.get('name', 'Разбор')} готов!</b>\n\n"
        "Сохраните это сообщение — в нём ваш персональный разбор.\n"
        "Хотите узнать ещё больше о себе?",
        reply_markup=to_catalog_kb(),
    )
