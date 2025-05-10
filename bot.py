from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
from datetime import datetime

# Конфигурация бота
TOKEN = 'YOUR_BOT_TOKEN'  # Замените на ваш токен
ADMIN_CHAT_ID = 'YOUR_CHAT_ID'  # Замените на ваш chat_id

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    if str(update.effective_chat.id) == ADMIN_CHAT_ID:
        await update.message.reply_text(
            "Добро пожаловать в панель управления заказами!\n\n"
            "Доступные команды:\n"
            "/orders - Показать все заказы\n"
            "/pending - Показать ожидающие заказы\n"
            "/help - Показать справку"
        )
    else:
        await update.message.reply_text("Извините, этот бот доступен только для администраторов.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    if str(update.effective_chat.id) == ADMIN_CHAT_ID:
        await update.message.reply_text(
            "Справка по командам:\n\n"
            "/orders - Показать все заказы\n"
            "/pending - Показать ожидающие заказы\n"
            "/confirm <order_id> - Подтвердить заказ\n"
            "/reject <order_id> - Отклонить заказ\n"
            "/status <order_id> - Показать статус заказа"
        )
    else:
        await update.message.reply_text("Извините, этот бот доступен только для администраторов.")

async def show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все заказы"""
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        return
    
    # Здесь должна быть логика получения заказов из базы данных
    # Это пример структуры сообщения
    message = "Список заказов:\n\n"
    message += "Заказ #123\n"
    message += "Статус: В обработке\n"
    message += "Сумма: 1000 ₽\n"
    message += "Дата: 01.01.2024\n\n"
    
    keyboard = [
        [
            InlineKeyboardButton("Подтвердить", callback_data="confirm_123"),
            InlineKeyboardButton("Отклонить", callback_data="reject_123")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def show_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать ожидающие заказы"""
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        return
    
    # Здесь должна быть логика получения ожидающих заказов
    message = "Ожидающие заказы:\n\n"
    message += "Заказ #123\n"
    message += "Статус: Ожидает подтверждения\n"
    message += "Сумма: 1000 ₽\n"
    message += "Дата: 01.01.2024\n\n"
    
    keyboard = [
        [
            InlineKeyboardButton("Подтвердить", callback_data="confirm_123"),
            InlineKeyboardButton("Отклонить", callback_data="reject_123")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if str(update.effective_chat.id) != ADMIN_CHAT_ID:
        await query.edit_message_text("Извините, этот бот доступен только для администраторов.")
        return
    
    action, order_id = query.data.split('_')
    
    if action == "confirm":
        # Здесь должна быть логика подтверждения заказа
        await query.edit_message_text(f"Заказ #{order_id} подтвержден!")
    elif action == "reject":
        # Здесь должна быть логика отклонения заказа
        await query.edit_message_text(f"Заказ #{order_id} отклонен!")

def main():
    """Запуск бота"""
    application = Application.builder().token(TOKEN).build()
    
    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("orders", show_orders))
    application.add_handler(CommandHandler("pending", show_pending))
    
    # Регистрация обработчика кнопок
    application.add_handler(telegram.ext.CallbackQueryHandler(button_callback))
    
    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main() 