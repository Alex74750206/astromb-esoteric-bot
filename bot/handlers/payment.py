from aiogram import Router, F
from aiogram.types import PreCheckoutQuery, Message

import database as db
from utils.delivery import deliver_reading

router = Router()


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    payment = message.successful_payment
    parts = payment.invoice_payload.split("|")
    product_id   = parts[0]
    birth_time   = parts[1] if len(parts) > 1 else ""
    birth_city   = parts[2] if len(parts) > 2 else ""
    forecast_year = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 2026

    user_id = message.from_user.id

    await db.add_purchase(
        user_id,
        product_id,
        payment.total_amount,
        payment.telegram_payment_charge_id,
    )

    await message.answer("🎉 <b>Оплата получена!</b> Готовлю ваш персональный разбор...")

    user = await db.get_user(user_id)
    birth_date = user.get("birth_date", "") if user else ""
    name = user.get("user_name_esoteric", "") if user else ""

    if not birth_date:
        await message.answer("⚠️ Не найдена дата рождения. Напишите /start и попробуйте снова.")
        return

    await deliver_reading(message, product_id, birth_date, name, birth_time, birth_city, year=forecast_year)
