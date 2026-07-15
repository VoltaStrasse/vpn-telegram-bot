import asyncio
import logging
import sqlite3
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from config import TOKEN, OPERATOR_ID, NOWPAYMENTS_API_KEY, WEBHOOK_HOST, WEBHOOK_PORT
from nowpayments import NowPayments

# ---------- Логирование ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- Инициализация ----------
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ---------- База данных ключей ----------
DB_NAME = "keys.db"

def init_db():
    """Создаёт таблицу keys, если её нет, и заполняет начальными ключами, если пусто."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_text TEXT UNIQUE,
                    used BOOLEAN DEFAULT 0
                )''')
    conn.commit()
    # Проверяем, есть ли ключи
    c.execute("SELECT COUNT(*) FROM keys")
    count = c.fetchone()[0]
    if count == 0:
        # Вставляем начальные ключи
        initial_keys = [
            "ssconf://connect.outlineaccesskey.com/ton/ru/e014d34bf3/3e2e9a4765#e014d34bf3",
            "ssconf://connect.outlineaccesskey.com/ton/ru/bc745ae0bf/11e3846634#bc745ae0bf",
            "ssconf://connect.outlineaccesskey.com/ton/ru/1e68174f6c/99861b6087#1e68174f6c",
            "ssconf://connect.outlineaccesskey.com/ton/ru/01c009c442/b08cebff12#01c009c442",
        ]
        for k in initial_keys:
            c.execute("INSERT INTO keys (key_text) VALUES (?)", (k,))
        conn.commit()
        logger.info(f"Inserted {len(initial_keys)} initial keys")
    conn.close()

def get_unused_key():
    """Возвращает случайный неиспользованный ключ и помечает его как used."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Получаем все unused ключи
    c.execute("SELECT id, key_text FROM keys WHERE used = 0")
    rows = c.fetchall()
    if not rows:
        conn.close()
        return None
    # Выбираем случайный
    key_id, key_text = random.choice(rows)
    c.execute("UPDATE keys SET used = 1 WHERE id = ?", (key_id,))
    conn.commit()
    conn.close()
    return key_text

# ---------- Глобальный объект оплаты ----------
payments = NowPayments(api_key=NOWPAYMENTS_API_KEY, webhook_path="/webhook")

# ---------- Колбэк при успешной оплате ----------
def on_payment_success(user_id: int, amount: float, invoice_id: str):
    logger.info(f"Payment success: user {user_id}, amount {amount}, invoice {invoice_id}")

    # Выдаём ключ пользователю
    key = get_unused_key()
    if key is None:
        msg = "❌ Извините, все ключи закончились. Обратитесь к оператору @VaultTechVPN."
        # Уведомляем оператора
        asyncio.create_task(
            bot.send_message(
                OPERATOR_ID,
                f"⚠️ Ключи закончились! Пользователь {user_id} оплатил, но ключей нет."
            )
        )
    else:
        msg = f"✅ Ваш ключ доступа:\n\n`{key}`\n\nСохраните его и используйте для подключения в Outline VPN. Инструкции по установке смотрите в боте."
        # Отправляем пользователю
        asyncio.create_task(
            bot.send_message(user_id, msg, parse_mode="Markdown")
        )

    # Уведомляем оператора
    asyncio.create_task(
        bot.send_message(
            OPERATOR_ID,
            f"✅ Оплата получена!\n"
            f"Пользователь ID: {user_id}\n"
            f"Сумма: {amount} USD\n"
            f"Инвойс: {invoice_id}\n"
            f"Ключ выдан автоматически."
        )
    )

# ---------- Клавиатуры ----------
def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📘 Инструкция"), KeyboardButton(text="📊 Тарифы")],
            [KeyboardButton(text="🚀 Купить"), KeyboardButton(text="🌟 Почему VaultTech?")],
        ],
        resize_keyboard=True
    )

def platforms_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Android"), KeyboardButton(text="🍏 iPhone/iOS")],
            [KeyboardButton(text="💻 Windows"), KeyboardButton(text="🍏 macOS")],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )

# ---------- /start ----------
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "🌟 Добро пожаловать в **VaultTech VPN**!\n\n"
        "Я — ваш проводник в мир безопасного и быстрого интернета. 🚀\n"
        "Здесь вы сможете приобрести ключ доступа к Outline VPN и получить всю необходимую информацию.\n\n"
        "📌 **Что я умею:**\n"
        "🔹 Инструкция — подробные гайды по установке на все устройства.\n"
        "🔹 Тарифы — актуальные цены и объёмы трафика.\n"
        "🔹 Купить — быстрый переход к оформлению подписки.\n"
        "🔹 Почему VaultTech? — узнайте, почему мы лучшие.\n\n"
        "Выберите действие ниже 👇",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

# ---------- Инструкция ----------
@dp.message(F.text == "📘 Инструкция")
async def instruction_cmd(message: types.Message):
    await message.answer(
        "Выберите платформу, на которую вы установите Outline VPN:",
        reply_markup=platforms_keyboard()
    )

@dp.message(F.text.in_(["📱 Android", "🍏 iPhone/iOS", "💻 Windows", "🍏 macOS"]))
async def platform_selected(message: types.Message):
    platform = message.text
    instructions = {
        "📱 Android": "📱 **Инструкция для Android**\n\n1️⃣ Установите приложение Outline VPN из GooglePlay (https://play.google.com/store/apps/details?id=org.outline.android.client) или с официального сайта (https://getoutline.org/ru/get-started/)\n2️⃣ Откройте приложение Outline VPN.\n3️⃣ Нажмите на знак (+) в правом верхнем углу, и нажмите кнопку 'Добавить сервер', далее вставьте ключ доступа, который вы получили (пример ключа: `ssconf://...`).\n4️⃣ Вы можете активировать его с помощью кнопки 'Подключиться', расположенной рядом с именем вашего профиля или нажав на большой круг в центре :)",
        "🍏 iPhone/iOS": "🍏 **Инструкция для iPhone/iOS**\n\n1️⃣ Установите приложение Outline VPN из AppStore (https://itunes.apple.com/us/app/outline-app/id1356177741) или с официального сайта (https://getoutline.org/ru/get-started/)\n2️⃣ Откройте приложение Outline VPN.\n3️⃣ Нажмите на знак (+) в правом верхнем углу, и нажмите кнопку 'Добавить сервер', далее вставьте ключ доступа, который вы получили (пример ключа: `ssconf://...`).\n4️⃣ Вы можете активировать его с помощью кнопки 'Подключиться', расположенной рядом с именем вашего профиля или нажав на большой круг в центре :)",
        "💻 Windows": "💻 **Инструкция для Windows**\n\n1️⃣ Установите приложение Outline VPN прямая ссылка для скачивания https://s3.amazonaws.com/outline-releases/client/windows/stable/Outline-Client.exe или с официального сайта (https://getoutline.org/ru/get-started/)\n2️⃣ Откройте приложение Outline VPN.\n3️⃣ Нажмите на знак (+) в правом верхнем углу, и нажмите кнопку 'Добавить сервер', далее вставьте ключ доступа, который вы получили (пример ключа: `ssconf://...`).\n4️⃣ Вы можете активировать его с помощью кнопки 'Подключиться', расположенной рядом с именем вашего профиля или нажав на большой круг в центре :)",
        "🍏 macOS": "🍏 **Инструкция для macOS**\n\n1️⃣ Установите приложение Outline VPN из AppStore (https://itunes.apple.com/us/app/outline-app/id1356178125) или с официального сайта (https://getoutline.org/ru/get-started/)\n2️⃣ Откройте приложение Outline VPN.\n3️⃣ Нажмите на знак (+) в правом верхнем углу, и нажмите кнопку 'Добавить сервер', далее вставьте ключ доступа, который вы получили (пример ключа: `ssconf://...`).\n4️⃣ Вы можете активировать его с помощью кнопки 'Подключиться', расположенной рядом с именем вашего профиля или нажав на большой круг в центре :)"
    }
    await message.answer(
        instructions[platform],
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

# ---------- Тарифы ----------
@dp.message(F.text == "📊 Тарифы")
async def price_cmd(message: types.Message):
    tariffs = (
        "📊 **Наши тарифы:**\n\n"
        "🔹 **100 ГБ** на 1 месяц — **550 ₽**\n"
        "🔹 **150 ГБ** на 3 месяца — **750 ₽**\n"
        "🔹 **300 ГБ** на 3 месяца — **850 ₽**\n"
        "🔹 **600 ГБ** на 12 месяцев — **1050 ₽**\n"
        "🔹 **1200 ГБ** на 12 месяцев — **1500 ₽**\n\n"
        "💡 Выберите подходящий вариант и нажмите **«Купить»**!"
    )
    await message.answer(tariffs, reply_markup=main_keyboard(), parse_mode="Markdown")

# ---------- Почему VaultTech? ----------
@dp.message(F.text == "🌟 Почему VaultTech?")
async def why_vaulttech(message: types.Message):
    text = (
        "🌟 **Почему выбирают VaultTech VPN?**\n\n"
        "Мы не просто продаём ключи — мы даём уверенность в стабильности и безопасности.\n\n"
        "🔹 **Надёжность, проверенная временем**\n"
        "Я лично мониторю ситуацию с блокировками VPN. У многих сервисов соединение начинает "
        "сбоить через месяц-два, а наш работает **уже 5 месяцев без единого перебоя**. "
        "Как только появляются новые способы блокировки, я мгновенно внедряю маскировку — "
        "вы всегда остаётесь в сети.\n\n"
        "🔹 **Мгновенная поддержка 24/7**\n"
        "Проблемы случаются, но мы решаем их моментально. Пишите в любое время — я отвечаю лично "
        "и помогаю восстановить соединение или выдаю новые ключи, если это необходимо.\n\n"
        "💬 **Никаких ботов-автоответчиков**, только живой человек, который понимает вашу проблему.\n\n"
        "✅ Выбирая нас, вы выбираете спокойствие и уверенность в том, что ваш доступ к интернету "
        "всегда будет защищён и доступен.\n\n"
        "🚀 Готовы попробовать? Нажмите **«Купить»** и начните уже сегодня!"
    )
    await message.answer(text, reply_markup=main_keyboard(), parse_mode="Markdown")

# ---------- Купить ----------
@dp.message(F.text == "🚀 Купить")
async def buy_cmd(message: types.Message):
    user_id = message.from_user.id

    invoice_url = await payments.create_invoice(user_id, amount=5.0, currency="usd")
    if not invoice_url:
        await message.answer(
            "❌ Ошибка создания счёта. Попробуйте позже или свяжитесь с @VaultTechVPN.",
            reply_markup=main_keyboard()
        )
        return

    await message.answer(
        f"💚 Спасибо за доверие!\n\n"
        f"Для оплаты перейдите по ссылке:\n{invoice_url}\n\n"
        f"После успешной оплаты ключ доступа будет выдан автоматически.\n"
        f"Обычно это занимает 5–10 минут.\n\n"
        f"Если возникнут вопросы — пишите оператору @VaultTechVPN.",
        reply_markup=main_keyboard(),
        disable_web_page_preview=True
    )

# ---------- Главное меню ----------
@dp.message(F.text == "🏠 Главное меню")
async def back_to_main(message: types.Message):
    await message.answer("🏠 Главное меню:", reply_markup=main_keyboard())

# ---------- Запуск ----------
async def main():
    # Инициализируем БД и ключи
    init_db()

    payments.set_on_payment_callback(on_payment_success)

    webhook_runner = await payments.start_webhook_server(host=WEBHOOK_HOST, port=WEBHOOK_PORT)
    logger.info("Webhook server started on %s:%s", WEBHOOK_HOST, WEBHOOK_PORT)

    logger.info("VPN Bot запущен (с поддержкой криптоплатежей)")
    try:
        await dp.start_polling(bot)
    finally:
        await webhook_runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())