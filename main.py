"""
Бот-магазин на aiogram 3.

Что умеет:
- показывает каталог товаров
- открывает карточку товара
- добавляет товары в корзину
- показывает корзину с суммой
- оформляет заказ и уведомляет администратора

Запуск:
    1. Получи токен у @BotFather
    2. Создай файл .env по образцу .env.example и впиши туда токен
    3. python main.py
"""

import asyncio
import json
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from dotenv import load_dotenv

import keyboards as kb
from catalog import get_product

# Загружаем переменные окружения из файла .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
# ADMIN_ID — твой Telegram id, чтобы получать уведомления о заказах.
# Узнать свой id можно у бота @userinfobot
ADMIN_ID = os.getenv("ADMIN_ID")
# PROXY_URL — прокси для доступа к Telegram, если API недоступен напрямую.
# Формат: http://user:pass@ip:port  или просто  http://ip:port
# Если оставить пустым — бот подключается к Telegram напрямую.
PROXY_URL = os.getenv("PROXY_URL")
# WEBAPP_URL — адрес Mini App (магазина-витрины). Обязательно HTTPS!
# Telegram не откроет Mini App по http:// или localhost.
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip()

# Защита от опечаток в .env: убираем задвоенный протокол
# (например 'https://https://site.com') и добавляем https://, если его нет.
if WEBAPP_URL:
    while WEBAPP_URL.startswith(("https://https://", "https://http://")):
        WEBAPP_URL = "https://" + WEBAPP_URL.split("://", 2)[-1]
    if not WEBAPP_URL.startswith("https://"):
        WEBAPP_URL = "https://" + WEBAPP_URL.removeprefix("http://")

logging.basicConfig(level=logging.INFO)

# Отладка: показываем, какой токен реально прочитался из .env (маскируем середину).
# repr() покажет скрытые кавычки или пробелы, если они случайно попали в .env.
if BOT_TOKEN:
    masked = BOT_TOKEN[:6] + "..." + BOT_TOKEN[-4:]
    logging.info("Токен прочитан: %s (длина %d)", repr(masked), len(BOT_TOKEN))
else:
    logging.info("Токен НЕ прочитан из .env!")

# Если задан прокси — создаём сессию через него, иначе подключаемся напрямую.
if PROXY_URL:
    session = AiohttpSession(proxy=PROXY_URL)
    bot = Bot(token=BOT_TOKEN, session=session)
    logging.info("Подключение к Telegram через прокси")
else:
    bot = Bot(token=BOT_TOKEN)

dp = Dispatcher()

# Корзины пользователей храним в памяти: {user_id: [product_id, product_id, ...]}
# Это учебный вариант. В реальном проекте — база данных, чтобы не терять данные при перезапуске.
carts: dict[int, list[int]] = {}


@dp.message(CommandStart())
async def start(message: Message):
    """Реакция на команду /start — приветствие и главное меню."""
    # Если задан WEBAPP_URL — даём кнопку Mini App у поля ввода
    if WEBAPP_URL:
        await message.answer(
            "Привет! Это демо-магазин.\n"
            "Жми «Открыть магазин» внизу — там витрина с корзиной.\n"
            "Или пользуйся кнопками в чате:",
            reply_markup=kb.webapp_menu(WEBAPP_URL),
        )
    await message.answer(
        "Выбери, что хочешь посмотреть:",
        reply_markup=kb.main_menu(),
    )


@dp.message(F.web_app_data)
async def webapp_order(message: Message):
    """
    Приём заказа из Mini App.

    Когда пользователь жмёт «Оформить заказ» в Mini App,
    приложение вызывает Telegram.WebApp.sendData(JSON),
    и Telegram доставляет это сюда в message.web_app_data.data.
    """
    try:
        order = json.loads(message.web_app_data.data)
    except (json.JSONDecodeError, AttributeError):
        await message.answer("Не удалось прочитать заказ, попробуй ещё раз.")
        return

    lines = [
        f"• {item['name']} × {item['qty']} — {item['price'] * item['qty']} ₽"
        for item in order.get("items", [])
    ]
    total = order.get("total", 0)

    # Подтверждение покупателю
    await message.answer(
        "Заказ из магазина оформлен!\n\n"
        + "\n".join(lines)
        + f"\n\nИтого: {total} ₽\nС вами скоро свяжутся. Спасибо!"
    )

    # Уведомление администратору
    if ADMIN_ID:
        user = message.from_user
        await bot.send_message(
            int(ADMIN_ID),
            f"Новый заказ из Mini App!\n"
            f"От: {user.full_name} (@{user.username})\n\n"
            + "\n".join(lines)
            + f"\n\nИтого: {total} ₽",
        )


@dp.callback_query(F.data == "menu")
async def show_menu(callback: CallbackQuery):
    """Вернуться в главное меню."""
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=kb.main_menu(),
    )
    await callback.answer()


@dp.callback_query(F.data == "catalog")
async def show_catalog(callback: CallbackQuery):
    """Показать список товаров."""
    await callback.message.edit_text(
        "Каталог товаров:",
        reply_markup=kb.catalog_menu(),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("product:"))
async def show_product(callback: CallbackQuery):
    """Показать карточку одного товара."""
    # callback.data выглядит как "product:1" — берём число после двоеточия
    product_id = int(callback.data.split(":")[1])
    product = get_product(product_id)

    if product is None:
        await callback.answer("Товар не найден", show_alert=True)
        return

    text = (
        f"<b>{product['name']}</b>\n\n"
        f"{product['description']}\n\n"
        f"Цена: {product['price']} ₽"
    )
    await callback.message.edit_text(
        text,
        reply_markup=kb.product_menu(product_id),
        parse_mode="HTML",
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("add:"))
async def add_to_cart(callback: CallbackQuery):
    """Добавить товар в корзину пользователя."""
    product_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    # Если корзины ещё нет — создаём пустую
    carts.setdefault(user_id, []).append(product_id)

    product = get_product(product_id)
    await callback.answer(f"{product['name']} добавлен в корзину")


@dp.callback_query(F.data == "cart")
async def show_cart(callback: CallbackQuery):
    """Показать содержимое корзины и общую сумму."""
    user_id = callback.from_user.id
    items = carts.get(user_id, [])

    if not items:
        await callback.message.edit_text(
            "Корзина пуста.",
            reply_markup=kb.main_menu(),
        )
        await callback.answer()
        return

    lines = []
    total = 0
    for product_id in items:
        product = get_product(product_id)
        lines.append(f"• {product['name']} — {product['price']} ₽")
        total += product["price"]

    text = "Ваша корзина:\n\n" + "\n".join(lines) + f"\n\nИтого: {total} ₽"
    await callback.message.edit_text(text, reply_markup=kb.cart_menu())
    await callback.answer()


@dp.callback_query(F.data == "clear")
async def clear_cart(callback: CallbackQuery):
    """Очистить корзину."""
    carts[callback.from_user.id] = []
    await callback.message.edit_text(
        "Корзина очищена.",
        reply_markup=kb.main_menu(),
    )
    await callback.answer()


@dp.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery):
    """Оформить заказ: сообщить пользователю и уведомить админа."""
    user_id = callback.from_user.id
    items = carts.get(user_id, [])

    if not items:
        await callback.answer("Корзина пуста", show_alert=True)
        return

    total = sum(get_product(pid)["price"] for pid in items)

    # Сообщаем покупателю
    await callback.message.edit_text(
        f"Заказ оформлен! Сумма: {total} ₽\n"
        "С вами скоро свяжутся. Спасибо за покупку!",
        reply_markup=kb.main_menu(),
    )

    # Уведомляем администратора (если задан ADMIN_ID)
    if ADMIN_ID:
        names = ", ".join(get_product(pid)["name"] for pid in items)
        user = callback.from_user
        await bot.send_message(
            int(ADMIN_ID),
            f"Новый заказ!\n"
            f"От: {user.full_name} (@{user.username})\n"
            f"Товары: {names}\n"
            f"Сумма: {total} ₽",
        )

    # Очищаем корзину после оформления
    carts[user_id] = []
    await callback.answer()


async def main():
    """Точка входа: запускаем опрос сообщений Telegram."""
    # Проверяем, что токен вообще загрузился из .env
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN не найден! Проверь, что рядом с main.py есть файл .env "
            "и в нём строка BOT_TOKEN=твой_токен"
        )

    # Убираем вебхук, если он был установлен раньше.
    # Пока стоит вебхук — обычный поллинг НЕ получает сообщения, и бот молчит.
    # drop_pending_updates=True очищает старые накопившиеся апдейты.
    await bot.delete_webhook(drop_pending_updates=True)

    me = await bot.get_me()
    logging.info("Бот запущен: @%s", me.username)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
