from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler,
)

# Этапы опроса
NAME, QUESTION_1, QUESTION_2, QUESTION_3, QUESTION_4, FILE = range(6)

# Словарь для хранения ответов
user_data = {}

# ID группового чата
GROUP_CHAT_ID = "-1002350744774"  # Убедитесь, что указан корректный ID беседы

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Отправляем сообщение с описанием, если чат пустой
    
    await update.message.reply_text("Введите ваше имя:")
    return NAME


# Обработка ответа на вопрос имени
async def question_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data[user_id] = {"name": update.message.text}
    await update.message.reply_text("Введите номер заказа:")
    return QUESTION_1

# Обработка ответа на 1 вопрос
async def question_1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data[user_id]["order_number"] = update.message.text
    await update.message.reply_text("Какие модули установлены и количество:")
    return QUESTION_2

# Обработка ответа на 2 вопрос
async def question_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data[user_id]["modules"] = update.message.text
    await update.message.reply_text("Потребляемая мощность вывески (Вт):")
    return QUESTION_3

# Обработка ответа на 3 вопрос
async def question_3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data[user_id]["power"] = update.message.text
    await update.message.reply_text("Установленный блок питания (Вт):")
    return QUESTION_4

# Обработка ответа на 4 вопрос
async def question_4(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data[user_id]["power_supply"] = update.message.text
    await update.message.reply_text("Теперь прикрепите одно или несколько фото.")
    return FILE

# Обработка прикреплённых файлов
async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id

    # Проверяем, прикреплено ли фото или документ
    if update.message.photo:
        if "photos" not in user_data[user_id]:
            user_data[user_id]["photos"] = []
        # Сохраняем ID фото
        user_data[user_id]["photos"].append(update.message.photo[-1].file_id)
        await update.message.reply_text("Фото добавлено. Добавьте ещё фото или нажмите 'Отправить'.", reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Отправить", callback_data='send_data')
        ]]))
        return FILE
    elif update.message.document:
        user_data[user_id]["file_type"] = "document"
        user_data[user_id]["file"] = update.message.document.file_id
    else:
        await update.message.reply_text("Пожалуйста, прикрепите фото или документ.")
        return FILE

# Обработка нажатия на кнопку "Отправить"
async def send_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.callback_query.from_user.id
    await update.callback_query.answer()  # Подтверждение нажатия

    # Формируем итоговое сообщение
    photos = user_data[user_id].get("photos", [])
    file_type = user_data[user_id].get("file_type")
    file_id = user_data[user_id].get("file")
    final_message = (
        f"Имя: {user_data[user_id]['name']}\n"
        f"Заказ номер {user_data[user_id]['order_number']}:\n"
        f"- Модули: {user_data[user_id]['modules']}\n"
        f"- Потребляемая мощность: {user_data[user_id]['power']} Вт\n"
        f"- Блок питания: {user_data[user_id]['power_supply']} Вт"
    )

    await context.bot.send_chat_action(chat_id=GROUP_CHAT_ID, action=ChatAction.TYPING)

    # Отправляем фото, если они есть
    if photos:
        # Создаем медиагруппу с фотографиями
        media = [InputMediaPhoto(media=photo) for photo in photos]
        await context.bot.send_media_group(chat_id=GROUP_CHAT_ID, media=media)

    # Отправляем текстовое сообщение с итоговыми данными
    await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=final_message)

    # Если прикреплен документ, отправляем его отдельно
    if file_type == "document":
        await context.bot.send_document(chat_id=GROUP_CHAT_ID, document=file_id)

    # Сообщаем пользователю об успешной отправке и добавляем кнопку "Начать"
    await update.callback_query.message.reply_text(
        "Спасибо! Ваши данные успешно отправлены.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Начать заново", callback_data="start_new")
        ]])
    )

    user_data.pop(user_id, None)

# Обработка нажатия на кнопку "Начать заново"
async def start_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Введите ваше имя:")
    return NAME

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Опрос отменён.")
    return ConversationHandler.END  # Завершаем разговор

# Главная функция
def main():
    token = "7772695373:AAGyPeKu_jOezmoxA0hN1swWXzwBulD7Qos"  # Замените на ваш токен

    # Создаём объект Application
    application = Application.builder().token(token).build()

    # Обработчик опроса
    conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_name)],
        QUESTION_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_1)],
        QUESTION_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_2)],
        QUESTION_3: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_3)],
        QUESTION_4: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_4)],
        FILE: [
            MessageHandler(filters.PHOTO | filters.Document.ALL, file_handler),
            CallbackQueryHandler(send_data, pattern='^send_data$'),
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        CallbackQueryHandler(start_new, pattern='^start_new$'),
    ],
)




    application.add_handler(conv_handler)

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()

