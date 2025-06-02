import os
from dotenv import load_dotenv

load_dotenv()

YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
YANDEX_OAUTH_TOKEN = os.getenv("YANDEX_OAUTH_TOKEN")
YANDEX_GPT_API_KEY = os.getenv("YANDEX_GPT_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")