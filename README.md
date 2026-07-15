# Demo-bot-shop — Telegram-магазин с Mini App

Демо интернет-магазина в Telegram: бот на Python (aiogram) + витрина как
Telegram Mini App. Покупатель может пользоваться и кнопками прямо в чате,
и полноценным веб-приложением внутри Telegram. Оформленный заказ приходит
администратору в личные сообщения.

## Демо

Видео работы: https://drive.google.com/file/d/1xhjGWRPO01eyyg6H1t2R2ZLyhnVCet8C/view?usp=sharing



## Возможности

- Каталог товаров с фото, ценами и описанием
- Два способа покупки: кнопки в чате и Mini App-витрина
- Корзина с изменением количества и подсчётом суммы
- Оформление заказа — уведомление админу в личку
- Тёмный интерфейс в стиле Telegram

## Как устроено

- **Бот** (`shop_bot/`) — Python + aiogram, обрабатывает команды и кнопки
- **Mini App** — витрина на Next.js, открывается внутри Telegram
- **Связь** — Mini App отправляет заказ боту через `web_app_data` (sendData)

## Стек

Python, aiogram, Next.js, TypeScript, Telegram Bot API, Telegram Mini Apps

## Запуск бота

1. Получи токен у [@BotFather](https://t.me/BotFather)
2. Скопируй `.env.example` в `.env` и впиши свои значения:
