import os
import logging
from datetime import datetime
from pathlib import Path

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputFile
)
from telegram.ext import (
    Application,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler
)

from dotenv import load_dotenv
import openpyxl
from openpyxl import Workbook

# === Загрузка токена ===
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ Токен не найден в .env")

# === Пути к файлам ===
BASE_DIR = Path("C:/Users/Леново/PycharmProjects/PythonProject").resolve()
WELCOME_PDF = BASE_DIR / "Добро пожаловать в Сбер окт 25 v2.pdf"
CARE_PDF = BASE_DIR / "Забота о сотрудниках-сжато.pdf"
PHOTO_P2P_PATH = BASE_DIR / "P2P.png"
PHOTO_CULTURE_PATH = BASE_DIR / "меро.png"
NEWS_PHOTO1 = BASE_DIR / "5460636998437042117.jpg"
NEWS_PHOTO2 = BASE_DIR / "5460636998437042118.jpg"
EXCEL_PATH = BASE_DIR / "users.xlsx"

# === Состояния ===
(
    ASK_NAME,
    ASK_TAB_NUMBER,
    ASK_FIRST_DAY,
    MAIN_MENU,
    FEEDBACK_LIKED,
    FEEDBACK_MISSING,
    FEEDBACK_SUGGEST
) = range(7)

# === Excel ===
def init_excel():
    if not EXCEL_PATH.exists():
        wb = Workbook()
        ws = wb.active
        ws.append([
            "Дата и время",
            "TG Username",
            "Имя (от пользователя)",
            "Табельный номер",
            "Дата первого рабочего дня",
            "User ID",
            "Что понравилось",
            "Чего не хватило",
            "Что добавить"
        ])
        wb.save(EXCEL_PATH)

def save_initial_data(user_id, username, name, tab_number, first_day):
    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb.active
    ws.append([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        username or "N/A",
        name,
        tab_number,
        first_day,
        user_id,
        "", "", ""
    ])
    wb.save(EXCEL_PATH)

def update_feedback_in_excel(user_id, liked, missing, suggest):
    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb.active
    for row in ws.iter_rows(min_row=2, values_only=False):
        if row[5].value == user_id:
            row[6].value = liked
            row[7].value = missing
            row[8].value = suggest
            break
    wb.save(EXCEL_PATH)

# === Клавиатуры ===
def get_main_menu():
    return ReplyKeyboardMarkup(
        [
            ["1. Сбер на Урале", "2. Видео"],
            ["3. Peer-to-peer", "4. Культура и сообщества"],
            ["5. Контакты", "6. Оставить обратную связь"],
            ["7. Забота", "8. Новости"]
        ],
        resize_keyboard=True
    )

def get_back_and_ask():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")],
        [InlineKeyboardButton("❓ Задать вопрос", callback_data="ask_question")]
    ])

# === Диалог знакомства ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("💬 Давай знакомиться! Напиши свое имя", reply_markup=ReplyKeyboardRemove())
    return ASK_NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("Пожалуйста, напиши своё имя.")
        return ASK_NAME
    context.user_data["name"] = name
    await update.message.reply_text("Напиши свой табельный номер, чтобы я мог найти тебя в системе 💯")
    return ASK_TAB_NUMBER

async def ask_tab_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tab = update.message.text.strip()
    if not tab.isdigit():
        await update.message.reply_text("Табельный номер должен состоять только из цифр. Попробуй снова:")
        return ASK_TAB_NUMBER
    context.user_data["tab_number"] = tab
    await update.message.reply_text(
        "📆 Напиши дату своего первого рабочего дня, чтобы мы могли присылать тебе уведомления и важные напоминания"
    )
    return ASK_FIRST_DAY

async def ask_first_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date_str = update.message.text.strip()
    try:
        datetime.strptime(date_str, "%d.%m.%Y")
    except ValueError:
        await update.message.reply_text("Неверный формат даты. Укажи в формате ДД.ММ.ГГГГ:")
        return ASK_FIRST_DAY

    context.user_data["first_day"] = date_str
    user = update.effective_user
    save_initial_data(
        user_id=user.id,
        username=user.username,
        name=context.user_data["name"],
        tab_number=context.user_data["tab_number"],
        first_day=date_str
    )

    await update.message.reply_text(
        "💚 Рад знакомству! Выбери пункт меню и изучай материалы:",
        reply_markup=get_main_menu()
    )
    return MAIN_MENU

# === Обработка меню ===
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "1. Сбер на Урале":
        await update.message.reply_text(
            "🧩 Самую важную информацию про Сбер и Урал я собрал для тебя в презентации — изучай, задавай вопросы, если есть!"
        )
        if WELCOME_PDF.exists():
            try:
                with open(WELCOME_PDF, 'rb') as f:
                    await update.message.reply_document(
                        document=InputFile(f, filename="Добро пожаловать в Сбер.pdf"),
                        reply_markup=get_back_and_ask()
                    )
            except Exception as e:
                await update.message.reply_text(f"⚠️ Ошибка: {str(e)}", reply_markup=get_back_and_ask())
        else:
            await update.message.reply_text("⚠️ Презентация не найдена.", reply_markup=get_back_and_ask())

    elif text == "2. Видео":
        await update.message.reply_text(
            "Ты стал частью большой команды Сбера и тебя приветствуют наши топ-менеджеры. Смотри видео 📽️.\n\n"
            "https://disk.yandex.ru/d/eAWTc08UnOBPwQ",
            reply_markup=get_back_and_ask()
        )

    elif text == "3. Peer-to-peer":
        msg = (
            "На всем периоде адаптации твоя основная поддержка - это HR-платформа Пульс и твой бадди.\n"
            "📌 Не забывай просматривать уведомления и задачи, проходи индивидуальный трек адаптации.\n\n"
            "🧬 Бадди - это один из представителей ролей взаимного развития (peer-to-peer).\n"
            "🖇️ Культура взаимного развития - это также консультанты по развитию, коучи, наставники, фасилитаторы, медиаторы. "
            "Подробнее ты сможешь ознакомиться в Пульс (раздел Развитие)."
        )
        await update.message.reply_text(msg)
        if PHOTO_P2P_PATH.exists():
            with open(PHOTO_P2P_PATH, 'rb') as f:
                await update.message.reply_photo(photo=InputFile(f), reply_markup=get_back_and_ask())
        else:
            await update.message.reply_text("🖼️ Схема временно недоступна.", reply_markup=get_back_and_ask())

    elif text == "4. Культура и сообщества":
        await update.message.reply_text(
            "Уральский банк живет насыщенной 🎨культурной и 🏆спортивной жизнью. "
            "Обязательно присоединяйся к мероприятиям - вся информация приходит тебе на почту. "
            "Вот несколько фото с последних событий:"
        )
        if PHOTO_CULTURE_PATH.exists():
            with open(PHOTO_CULTURE_PATH, 'rb') as f:
                await update.message.reply_photo(photo=InputFile(f))
        else:
            await update.message.reply_text("⚠️ Фото не найдено.")

        await update.message.reply_text(
            "Вступай в сообщества Уральского банка — будь в курсе событий!\n\n"
            "📢️ **Телеграм-канал «Говорит Урал»** — новости, анонсы и важные события\n"
            "🎗️ **Телеграм-канал «Биржа волонтёров Екатеринбург (УБ)»** — волонтёрские активности, поддержка и вдохновение\n\n"
            "Ссылки на каналы указаны в презентации, которую ты уже изучил.\n"
            "Если остались вопросы — пиши в раздел **«Контакты»**!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")]
            ])
        )

    elif text == "5. Контакты":
        await update.message.reply_text(
            "📨 Любые вопросы направляй на почту куратора по адаптации в Уральском банке "
            "Котельниковой Кристине Kotelnikova.K.A@sberbank.ru",
            reply_markup=get_back_and_ask()
        )

    elif text == "6. Оставить обратную связь":
        await update.message.reply_text(
            "Спасибо, что хочешь помочь нам стать лучше!🔑Ответь, пожалуйста, на три коротких вопроса.",
            reply_markup=ReplyKeyboardRemove()
        )
        await update.message.reply_text("🟢 Опиши, что понравилось при использовании бота:")
        return FEEDBACK_LIKED

    elif text == "7. Забота":
        await update.message.reply_text(
            "☀️ Это все мое - о поддержке, льготах и возможностях для личного и профессионального роста в Сбере!"
        )
        if CARE_PDF.exists():
            try:
                with open(CARE_PDF, 'rb') as f:
                    await update.message.reply_document(
                        document=InputFile(f, filename="Забота о сотрудниках.pdf"),
                        reply_markup=get_back_and_ask()
                    )
            except Exception as e:
                await update.message.reply_text(f"⚠️ Ошибка: {str(e)}", reply_markup=get_back_and_ask())
        else:
            await update.message.reply_text("⚠️ Презентация не найдена.", reply_markup=get_back_and_ask())

    elif text == "8. Новости":
        news_text = (
            "⚡ 22 октября в Технохабе Екатеринбурга прошла встреча Вице-президента-председателя Колтыпина Петра Николаевича "
            "и Заместителя председателя, руководителя блока Люди и культура Осиповой Марии Леонидовны с новыми сотрудниками "
            "команды Сбера на Урале. На встрече обсудили особенности бизнеса на Урале, какими качествами и ценностями должны "
            "обладать сотрудники Сбера и как достигать карьерных высот. Такие мероприятия заряжают энергией и успехом!"
        )
        await update.message.reply_text(news_text)

        # Отправка двух фото
        photos_sent = 0
        for photo_path in [NEWS_PHOTO1, NEWS_PHOTO2]:
            if photo_path.exists():
                try:
                    with open(photo_path, 'rb') as f:
                        await update.message.reply_photo(photo=InputFile(f))
                    photos_sent += 1
                except Exception as e:
                    await update.message.reply_text(f"⚠️ Не удалось отправить фото: {str(e)}")
            else:
                await update.message.reply_text(f"⚠️ Фото не найдено: {photo_path.name}")

        if photos_sent > 0:
            await update.message.reply_text("Фото с мероприятия 👆", reply_markup=get_back_and_ask())
        else:
            await update.message.reply_text("Фото с мероприятия временно недоступны.", reply_markup=get_back_and_ask())

    return MAIN_MENU

# === Обратная связь ===
async def feedback_liked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    liked = update.message.text.strip()
    context.user_data["feedback_liked"] = liked
    await update.message.reply_text("🟢 Напиши, чего тебе не хватило при использовании бота:")
    return FEEDBACK_MISSING

async def feedback_missing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    missing = update.message.text.strip()
    context.user_data["feedback_missing"] = missing
    await update.message.reply_text("🟢 Что можно добавить в чат-бот, чтобы его использование было максимально полезным для новых сотрудников?")
    return FEEDBACK_SUGGEST

async def feedback_suggest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    suggest = update.message.text.strip()
    user = update.effective_user
    update_feedback_in_excel(user.id, context.user_data.get("feedback_liked", ""), context.user_data.get("feedback_missing", ""), suggest)
    await update.message.reply_text(
        "🙌 Благодарим за твою обратную связь! Это очень важно для дальнейшего развития нашего виртуального помощника!✨\n"
        "🎁 Среди всех участников опроса первого числа каждого календарного месяца мы будем разыгрывать памятный мерч👕 — следи за уведомлениями!",
        reply_markup=get_main_menu()
    )
    return MAIN_MENU

# === Обработка кнопок ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "back_to_menu":
        await query.message.reply_text("Выбери пункт меню:", reply_markup=get_main_menu())
    elif query.data == "ask_question":
        await query.message.reply_text(
            "Напиши свой вопрос — мы обязательно ответим!",
            reply_markup=ReplyKeyboardMarkup([["⬅️ Вернуться в меню"]], resize_keyboard=True)
        )

async def handle_return(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ Вернуться в меню":
        await update.message.reply_text("Выбери пункт меню:", reply_markup=get_main_menu())
        return MAIN_MENU
    await update.message.reply_text("Спасибо за вопрос!", reply_markup=get_main_menu())
    return MAIN_MENU

# === Запуск ===
def main():
    print(f"📁 Папка: {BASE_DIR}")
    print(f"📄 Добро пожаловать.pdf: {'✅' if WELCOME_PDF.exists() else '❌'}")
    print(f"📄 Забота.pdf: {'✅' if CARE_PDF.exists() else '❌'}")
    print(f"🖼️ Новости фото 1: {'✅' if NEWS_PHOTO1.exists() else '❌'}")
    print(f"🖼️ Новости фото 2: {'✅' if NEWS_PHOTO2.exists() else '❌'}")
    init_excel()
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_TAB_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_tab_number)],
            ASK_FIRST_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_first_day)],
            MAIN_MENU: [
                MessageHandler(filters.Regex("^⬅️ Вернуться в меню$"), handle_return),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)
            ],
            FEEDBACK_LIKED: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_liked)],
            FEEDBACK_MISSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_missing)],
            FEEDBACK_SUGGEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_suggest)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()