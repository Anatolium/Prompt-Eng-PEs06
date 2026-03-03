import logging
import re

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.error import BadRequest

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from get_env import TELEGRAM_TOKEN, YANDEX_CLOUD_API_KEY, YANDEX_CLOUD_FOLDER

# --- Логирование ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Инициализация клиента YandexGPT ---
llm = ChatOpenAI(
    model=f"gpt://{YANDEX_CLOUD_FOLDER}/yandexgpt-lite/latest",
    temperature=0.2,
    api_key=YANDEX_CLOUD_API_KEY,
    base_url="https://ai.api.cloud.yandex.net/v1",
    timeout=180,
    max_retries=3,
)

# =========================
# 🔧 Обработка Markdown
# =========================

MDV2_ESCAPE_CHARS = r"_*[]()~`>#+-=|{}.!"


def fix_unclosed_codeblocks(text: str) -> str:
    """Закрывает незакрытые ``` блоки"""
    if text.count("```") % 2 != 0:
        text += "\n```"
    return text


def convert_double_bold(text: str) -> str:
    """**text** -> *text*"""
    return re.sub(r"\*\*(.*?)\*\*", r"*\1*", text, flags=re.DOTALL)


def escape_markdown_v2(text: str) -> str:
    """Экранирует спецсимволы MarkdownV2"""
    return re.sub(
        f"([{re.escape(MDV2_ESCAPE_CHARS)}])",
        r"\\\1",
        text,
    )


def restore_formatting(text: str) -> str:
    """
    Возвращает рабочие markdown-символы после escape
    """
    # возвращаем жирный
    text = text.replace(r"\*", "*")

    # возвращаем code blocks
    text = text.replace(r"\`", "`")

    return text


def prepare_markdown(text: str) -> str:
    """
    Полная подготовка текста для Telegram MarkdownV2
    """
    text = fix_unclosed_codeblocks(text)
    text = convert_double_bold(text)
    text = escape_markdown_v2(text)
    text = restore_formatting(text)
    return text


async def safe_edit_message(message, text: str):
    """
    Пытается отправить MarkdownV2.
    Если Telegram ругнулся — отправляет plain text.
    """
    try:
        prepared = prepare_markdown(text)
        await message.edit_text(prepared, parse_mode="MarkdownV2")
    except BadRequest as e:
        logger.warning(f"Markdown сломался, fallback в plain text: {e}")
        await message.edit_text(text)


# =========================
# 🤖 Telegram handlers
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот-помощник через YandexGPT.\n"
        "Отправь любое сообщение, и я создам учебный материал."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    status_msg = await update.message.reply_text(
        "⏳ Обрабатываю запрос через YandexGPT..."
    )

    try:
        messages = [
            HumanMessage(content=user_message),
        ]

        # Вызов модели
        resp = llm.invoke(messages)

        response_text = resp.content if resp else "Нет ответа от YandexGPT."

        await safe_edit_message(status_msg, response_text)

    except Exception as e:
        logger.error(e)
        await update.message.reply_text(
            "Ошибка при обработке запроса. Попробуйте позже."
        )


# =========================
# 🚀 Запуск
# =========================

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
