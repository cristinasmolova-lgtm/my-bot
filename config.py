# config.py (ВРЕМЕННОЕ ИЗМЕНЕНИЕ ДЛЯ ТЕСТА)
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла (если он есть)
# load_dotenv() # <-- Закомментируйте эту строку

# Токен бота, полученный от @BotFather
# Значение по умолчанию "YOUR_BOT_TOKEN_HERE" будет использовано, если переменная BOT_TOKEN не найдена в .env
# ВРЕМЕННО УКАЖИТЕ ТОКЕН НАПРЯМУЮ:
BOT_TOKEN = "8463773957:AAEvGphKRfZlKJNMXcS9n5bhuXiqwdVKfpE" # ЗАМЕНИТЕ НА ВАШ РЕАЛЬНЫЙ ТОКЕН!
# ИЛИ, если хотите использовать .env, убедитесь, что load_dotenv() НЕ закомментирована и .env корректен:
# BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Путь к файлу Excel
EXCEL_FILE_PATH = "data/users_data.xlsx"

# Пути к файлам
PDF_PATH_1 = "documents/День новичка в2 compressed.pdf"
PDF_PATH_2 = "documents/Забота о сотрудниках-сжато.pdf"
P2P_IMAGE_PATH = "images/P2P.png"
EVENT_IMAGE_PATH = "images/меро.png"
NEWS_IMAGE_PATH_1 = "images/5460636998437042117.jpg"
NEWS_IMAGE_PATH_2 = "images/5460636998437042118.jpg"

# Ссылка на видео
YANDEX_DISK_URL = "https://disk.yandex.ru/d/eAWTc08UnOBPwQ"
CONTACT_EMAIL = "Kotelnikova.K.A@sberbank.ru"
