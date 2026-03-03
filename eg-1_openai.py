# Тип взаимодействия: Stateful (поток с историей диалога)
# Хранение контекста: Thread сохраняет историю переписки
# Код помнит предыдущие сообщения в рамках thread
# Промпт вынесен в ассистента (ASSISTANT_ID)
# История хранится на стороне OpenAI
# Можно продолжить диалог позже, по thread_id, даже после перезапуска бота
import logging  # Импортируем модуль для логирования событий в приложении
from openai import OpenAI  # Импортируем класс OpenAI для работы с API OpenAI
from telegram import Update  # Импортируем класс Update для обработки обновлений Telegram
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

from get_env import OPENAI_API_KEY, ASSISTANT_ID, TELEGRAM_TOKEN  # Импортируем ключи и токены из локального модуля

# --- Инициализация клиентов ---
client = OpenAI(api_key=OPENAI_API_KEY)  # Создаём клиент OpenAI, передавая API-ключ

# --- Логирование ---
logging.basicConfig(level=logging.INFO)  # Устанавливаем базовый уровень логирования — INFO
logger = logging.getLogger(__name__)  # Получаем объект логгера для текущего модуля
user_threads = {}  # Создаём словарь для хранения данных потоков пользователей


# --- Приветственное сообщение ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Обработчик команды /start — отправляет приветственное сообщение
    await update.message.reply_text(
        "👋 Привет! Я бот-помощник.\n"
        "Отправь любое сообщение, и я передам его ассистенту OpenAI."
    )


# --- Основная логика ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text  # Получаем текст сообщения пользователя
    user_id = update.message.from_user.id  # Получаем идентификатор пользователя

    status_msg = await update.message.reply_text("Обрабатываю запрос...")  # Сообщаем пользователю о процессе обработки

    try:
        # --- Работа с потоками OpenAI ---
        if user_id in user_threads:  # Проверяем, есть ли уже поток для пользователя
            thread_id = user_threads[user_id]  # Если есть, получаем его id
        else:
            thread = client.beta.threads.create()  # Иначе создаём новый поток в OpenAI
            thread_id = thread.id  # Получаем id нового потока
            user_threads[user_id] = thread_id  # Сохраняем его для конкретного пользователя

        # Отправляем сообщение пользователя в созданный поток OpenAI
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )

        # Запускаем ассистента для обработки потока
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )

        # Ожидаем завершения обработки (пока статус - в очереди или выполняется)
        while run.status in ("queued", "in_progress"):
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )

        # Получаем список всех сообщений в потоке
        messages = client.beta.threads.messages.list(thread_id=thread_id)

        # Извлекаем ответы ассистента из сообщений потока
        response_texts = [
            msg.content[0].text.value
            for msg in reversed(messages.data)
            if msg.role == "assistant"
        ]

        # Собираем все ответы ассистента в одну строку, если они есть, иначе выводим сообщение об отсутствии ответа
        response = "\n".join(response_texts) if response_texts else "Нет ответа от ассистента."
        await status_msg.edit_text(response)  # Обновляем статусное сообщение на ответ ассистента

    except Exception as e:
        logger.error(e)  # Логируем ошибку
        await update.message.reply_text("Ошибка при обработке запроса. Попробуйте позже.")


# --- Запуск бота ---
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()  # Инициализируем приложение Telegram бота

    # Добавляем обработчик команды /start
    app.add_handler(CommandHandler("start", start))
    # Добавляем обработчик всех текстовых сообщений, кроме команд
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен!")
    app.run_polling()  # Запускаем бесконечный цикл ожидания событий (polling)


if __name__ == "__main__":
    main()
