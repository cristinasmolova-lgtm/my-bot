import os
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Пути
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MEDIA_DIR = BASE_DIR / "media"
EXCEL_PATH = DATA_DIR / "users.xlsx"

# Создаём папки и файл, если не существует
DATA_DIR.mkdir(exist_ok=True)
if not EXCEL_PATH.exists():
    df = pd.DataFrame(columns=[
        "datetime", "tg_username", "name", "employee_id", "start_date",
        "user_id", "raw_input", "feedback_q1", "feedback_q2", "feedback_q3", "question"
    ])
    df.to_excel(EXCEL_PATH, index=False)

# Состояния
(
    ASK_NAME,
    ASK_EMPLOYEE_ID,
    ASK_START_DATE,
    MAIN_MENU,
    FEEDBACK_Q1,
    FEEDBACK_Q2,
    FEEDBACK_Q3,
) = range(7)


def get_main_keyboard():
    """Основное меню: 2 столбца по 4 кнопки + 'Задать вопрос' снизу."""
    return [
        ["1. Сбер на Урале", "2. Видео"],
        ["3. Peer-to-peer", "4. Культура и сообщества"],
        ["5. Это все мое", "6. Контакты"],
        ["7. Оставить обратную связь", "8. Новости"],
        ["Задать вопрос"]
    ]


# === Обработчики регистрации (без кнопки "Задать вопрос") ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data.clear()
    context.user_data['user_id'] = user.id
    context.user_data['tg_username'] = user.username or "Не указан"
    context.user_data['datetime'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    await update.message.reply_text(
        "💬Давай знакомиться! Напиши свое имя",
        reply_markup=None  # Без клавиатуры
    )
    return ASK_NAME


async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("Пожалуйста, введи своё имя.")
        return ASK_NAME

    context.user_data['name'] = name
    await update.message.reply_text("Напиши свой табельный номер, чтобы я мог найти в системе💯")
    return ASK_EMPLOYEE_ID


async def ask_employee_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emp_id = update.message.text.strip()
    if not emp_id:
        await update.message.reply_text("Пожалуйста, введи табельный номер.")
        return ASK_EMPLOYEE_ID

    context.user_data['employee_id'] = emp_id
    await update.message.reply_text("📆Напиши дату своего первого рабочего дня (в формате ДД.ММ.ГГГГ), чтобы мы могли присылать тебе уведомления и важные напоминания.")
    return ASK_START_DATE


async def ask_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date_str = update.message.text.strip()
    try:
        datetime.strptime(date_str, "%d.%m.%Y")
    except ValueError:
        await update.message.reply_text("Пожалуйста, введи дату в формате ДД.ММ.ГГГГ")
        return ASK_START_DATE

    context.user_data['start_date'] = date_str

    # Сохраняем в Excel
    new_row = {
        "datetime": context.user_data['datetime'],
        "tg_username": context.user_data['tg_username'],
        "name": context.user_data['name'],
        "employee_id": context.user_data['employee_id'],
        "start_date": context.user_data['start_date'],
        "user_id": context.user_data['user_id'],
        "raw_input": f"{context.user_data['name']} | {context.user_data['employee_id']} | {context.user_data['start_date']}",
        "feedback_q1": "",
        "feedback_q2": "",
        "feedback_q3": "",
        "question": ""
    }
    df = pd.read_excel(EXCEL_PATH)
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_excel(EXCEL_PATH, index=False)

    await update.message.reply_text(
        "💚Рад знакомству! Выбери пункт меню и изучай материалы:",
        reply_markup=ReplyKeyboardMarkup(get_main_keyboard(), resize_keyboard=True)
    )
    return MAIN_MENU


# === Основное меню и обработка ===

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text

    if choice == "💬Задать вопрос":
        # Просто запрашиваем текст вопроса — без смены состояния
        await update.message.reply_text("Напиши свой вопрос:")
        return MAIN_MENU  # Остаёмся в MAIN_MENU, но ждём текст

    # Если пользователь прислал произвольный текст (в т.ч. вопрос) — обрабатываем как вопрос
    if choice not in [
        "1. Сбер на Урале", "2. Видео", "3. Peer-to-peer", "4. Культура и сообщества",
        "5. Это все мое", "6. Контакты", "7. Оставить обратную связь", "8. Новости"
    ]:
        # Это вопрос!
        user_id = context.user_data.get('user_id')
        question_text = choice

        # Сохраняем в Excel
        df = pd.read_excel(EXCEL_PATH)
        idx = df[df['user_id'] == user_id].index
        if not idx.empty:
            df.loc[idx, 'question'] = question_text
            df.to_excel(EXCEL_PATH, index=False)
        else:
            # На случай, если что-то пошло не так
            new_row = {
                "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tg_username": context.user_data.get('tg_username', "Неизвестно"),
                "name": "",
                "employee_id": "",
                "start_date": "",
                "user_id": user_id,
                "raw_input": "",
                "feedback_q1": "",
                "feedback_q2": "",
                "feedback_q3": "",
                "question": question_text
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_excel(EXCEL_PATH, index=False)

        await update.message.reply_text("Благодарим за твой вопрос. Взяли в работу, вернемся с ответом👍")
        return MAIN_MENU

    # Обработка пунктов меню
    if choice == "1. Сбер на Урале":
        await update.message.reply_text("🧩Самую важную информацию про Сбер и Урал я собрал для тебя в презентации - изучай, задавай вопросы, если есть")
        await update.message.reply_document(document=open(MEDIA_DIR / "Sber_Ural.pdf", "rb"))

    elif choice == "2. Видео":
        await update.message.reply_text("Ты стал частью большой команды Сбера и тебя приветствуют наши топ-менеджеры. Смотри видео📽️")
        await update.message.reply_text("https://disk.yandex.ru/d/eAWTc08UnOBPwQ")

    elif choice == "3. Peer-to-peer":
        await update.message.reply_text(
            "На всем периоде адаптации твоя основная поддержка - это HR-платформа Пульс и твой бадди.\n"
            "📌Не забывай просматривать уведомления и задачи, проходи индивидуальный трек адаптации\n"
            "🧬Бадди - это один из представителей ролей взаимного развития (peer-to-peer).\n"
            "Культура взаимного развития - это также консультанты по развитию, коучи, наставники, фасилитаторы, медиаторы. Подробнее ты сможешь ознакомиться в Пульс (раздел Развитие)."
        )
        await update.message.reply_photo(photo=open(MEDIA_DIR / "Р2Р (1).png", "rb"))

    elif choice == "4. Культура и сообщества":
        await update.message.reply_text("Уральский банк живет насыщенной 🎨 культурной и 🏆 спортивной жизнью. Обязательно присоединяйся к мероприятиям - вся информация приходит тебе на почту. Вот несколько фото с последних событий")
        await update.message.reply_photo(photo=open(MEDIA_DIR / "меро (1).png", "rb"))
        await update.message.reply_text(
            "Вступай в сообщества Уральского банка - будь в курсе событий!\n"
            " 📢Телеграм-канал \"Говорит Урал\" — новости, анонсы, важные события\n"
            " 🎗️Телеграм-канал \"Биржа волонтёров Екатеринбург (УБ)\" — анонсы, поддержка, активности Сбер.\n"
            "Ссылки на каналы находятся в презентации, которую ты изучил выше. Вопросы? Пиши в раздел «Контакты»!"
        )

    elif choice == "5. Это все мое":
        await update.message.reply_text("🫂Сбер заботится о своих сотрудниках с самого первого дня работы. В презентации собрали для вас все корпоративные льготы и привилегии. Изучай, пользуйся - ведь это все твое!")
        await update.message.reply_document(document=open(MEDIA_DIR / "Care_for_employees.pdf", "rb"))

    elif choice == "6. Контакты":
        await update.message.reply_text("📨Любые вопросы направляй на почту куратора по адаптации в Уральском банке Котельниковой Кристине Kotelnikova.K.A@sberbank.ru")

    elif choice == "7. Оставить обратную связь":
        await update.message.reply_text("Спасибо, что помогаешь нам стать лучше! 🔑 Ответь, пожалуйста, на три коротких вопроса:")
        await update.message.reply_text("🟢 Опиши, что понравилось при использовании бота:")
        return FEEDBACK_Q1

    elif choice == "8. Новости":
        await update.message.reply_text(
            "22 октября в Технохабе Екатеринбурга прошла встреча Вице-президента-председателя Колтыпина Петра Николаевича и Заместителя председателя, руководителя блока Люди и культура Осиповой Марии Леонидовны с новыми сотрудниками команды Сбера на Урале. "
            "На встрече обсудили особенности бизнеса на Урале, какими качествами и ценностями должны обладать сотрудники Сбера и как достигать карьерных высот. "
            "Такие мероприятия заряжают энергией и успехом!"
        )
        await update.message.reply_photo(photo=open(MEDIA_DIR / "новость2.jpg", "rb"))

    return MAIN_MENU


# === Обратная связь ===

async def feedback_q1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fb_q1'] = update.message.text
    await update.message.reply_text("🟢 Напиши, чего тебе не хватило при использовании бота:")
    return FEEDBACK_Q2


async def feedback_q2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fb_q2'] = update.message.text
    await update.message.reply_text("🟢 Что можно добавить в чат-бот, чтобы его использование было максимально полезным для новых сотрудников?")
    return FEEDBACK_Q3


async def feedback_q3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fb_q3'] = update.message.text

    df = pd.read_excel(EXCEL_PATH)
    user_id = context.user_data['user_id']
    idx = df[df['user_id'] == user_id].index
    if not idx.empty:
        df.loc[idx, 'feedback_q1'] = context.user_data.get('fb_q1', "")
        df.loc[idx, 'feedback_q2'] = context.user_data.get('fb_q2', "")
        df.loc[idx, 'feedback_q3'] = context.user_data.get('fb_q3', "")
        df.to_excel(EXCEL_PATH, index=False)

    await update.message.reply_text(
        "Благодарим за обратную связь, это очень важно для дальнейшего развития нашего виртуального помощника.\n"
        "🎁 Среди всех участников опроса первого числа каждого календарного месяца мы будем разыгрывать памятный мерч - следи за уведомлениями!⚡",
        reply_markup=ReplyKeyboardMarkup(get_main_keyboard(), resize_keyboard=True)
    )
    return MAIN_MENU


# === Запуск ===

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN не указан в .env")

    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_EMPLOYEE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_employee_id)],
            ASK_START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_start_date)],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)],
            FEEDBACK_Q1: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_q1)],
            FEEDBACK_Q2: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_q2)],
            FEEDBACK_Q3: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_q3)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    logger.info("✅ Бот запущен!")
    application.run_polling()


if __name__ == "__main__":
    main()




