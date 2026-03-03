import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("PROXYAPI_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

YANDEX_CLOUD_FOLDER = os.getenv("YANDEX_CLOUD_FOLDER")
YANDEX_CLOUD_API_KEY = os.getenv("YANDEX_CLOUD_API_KEY")

ASSISTANT_ID = os.getenv("ASSISTANT_ID")
GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")

LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_BASE_URL = os.getenv("LANGFUSE_BASE_URL")  # Получаем адрес или домен сервиса Langfuse
