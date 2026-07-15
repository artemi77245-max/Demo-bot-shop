"""
Клавиатуры (кнопки) для бота.

Здесь мы собираем инлайн-кнопки, которые видит пользователь.
Вынесли их в отдельный файл, чтобы main.py не разрастался.
"""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from catalog import PRODUCTS


def webapp_menu(webapp_url: str) -> ReplyKeyboardMarkup:
    """
    Кнопка, открывающая Mini App (магазин-витрину).

    ВАЖНО: это именно ReplyKeyboardMarkup (кнопка у поля ввода),
    а не инлайн-кнопка. Только через такую кнопку Mini App может
    отправить данные боту через sendData (web_app_data).
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="Открыть магазин",
                    web_app=WebAppInfo(url=webapp_url),
                )
            ]
        ],
        resize_keyboard=True,
    )


def main_menu() -> InlineKeyboardMarkup:
    """Главное меню: каталог и корзина."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Каталог", callback_data="catalog")
    builder.button(text="Корзина", callback_data="cart")
    builder.adjust(2)  # обе кнопки в один ряд
    return builder.as_markup()


def catalog_menu() -> InlineKeyboardMarkup:
    """Список товаров — по кнопке на каждый товар."""
    builder = InlineKeyboardBuilder()
    for product in PRODUCTS:
        # callback_data кодирует действие и id товара, например "product:1"
        builder.button(
            text=f"{product['name']} — {product['price']} ₽",
            callback_data=f"product:{product['id']}",
        )
    builder.button(text="⬅ Назад", callback_data="menu")
    builder.adjust(1)  # каждый товар с новой строки
    return builder.as_markup()


def product_menu(product_id: int) -> InlineKeyboardMarkup:
    """Кнопки на карточке товара: добавить в корзину или назад."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Добавить в корзину", callback_data=f"add:{product_id}")
    builder.button(text="⬅ К каталогу", callback_data="catalog")
    builder.adjust(1)
    return builder.as_markup()


def cart_menu() -> InlineKeyboardMarkup:
    """Кнопки в корзине: оформить заказ, очистить, назад."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Оформить заказ", callback_data="checkout")
    builder.button(text="Очистить корзину", callback_data="clear")
    builder.button(text="⬅ В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()
