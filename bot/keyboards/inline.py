from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import PRODUCTS


def welcome_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✨ Узнать своё Число Судьбы бесплатно", callback_data="lead_magnet")
    builder.adjust(1)
    return builder.as_markup()


def after_free_reading_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔮 Открыть каталог разборов", callback_data="catalog")
    builder.adjust(1)
    return builder.as_markup()


def catalog_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for pid, product in PRODUCTS.items():
        builder.button(
            text=f"{product['name']} — {product['price_stars']} ⭐",
            callback_data=f"product:{pid}",
        )
    builder.adjust(1)
    return builder.as_markup()


def product_kb(product_id: str, already_purchased: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if already_purchased:
        builder.button(text="✅ Уже куплено — получить снова", callback_data=f"buy:{product_id}")
    else:
        product = PRODUCTS[product_id]
        builder.button(
            text=f"💫 Купить за {product['price_stars']} ⭐ Stars",
            callback_data=f"buy:{product_id}",
        )
    builder.button(text="← Назад в каталог", callback_data="catalog")
    builder.adjust(1)
    return builder.as_markup()


def to_catalog_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔮 В каталог разборов", callback_data="catalog")
    builder.adjust(1)
    return builder.as_markup()
