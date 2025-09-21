from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import os

# ТВОЙ ТОКЕН БОТА ИЗ BOTFATHER
BOT_TOKEN = ""

# Список вопросов и ответов для викторины
QUESTIONS = [
    {
        "question": "Какая столица Японии?",
        "answer": "Токио"
    },
    {
        "question": "Кто написал 'Войну и мир'?",
        "answer": "Лев Толстой"
    },
    {
        "question": "Какая самая высокая гора в мире?",
        "answer": "Эверест"
    },
    {
        "question": "Сколько континентов на Земле?",
        "answer": "7"
    },
    {
        "question": "Какое животное является символом Австралии?",
        "answer": "Кенгуру"
    }
]

# Команда /start - запускает викторину
async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Устанавливаем начальное состояние
    context.user_data['score'] = 0
    context.user_data['current_question_index'] = 0
    context.user_data['is_awaiting_answer'] = True
    context.user_data['timer_task'] = None

    await update.message.reply_text("Привет! Начнем викторину! У тебя 15 секунд на каждый вопрос.")
    await send_next_question(update, context)

# Команда /stop - останавливает викторину
async def stop_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'current_question_index' in context.user_data:
        del context.user_data['current_question_index']
        if context.user_data.get('timer_task'):
            context.user_data['timer_task'].cancel()
        await update.message.reply_text("Викторина остановлена. Чтобы начать заново, отправь /start.")
    else:
        await update.message.reply_text("Викторина не запущена.")

# Отправляет следующий вопрос и запускает таймер
async def send_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_index = context.user_data.get('current_question_index')

    if current_index >= len(QUESTIONS):
        final_score = context.user_data['score']
        await update.message.reply_text(f"Викторина окончена! Твой результат: {final_score} из {len(QUESTIONS)}. Спасибо за участие!")
        del context.user_data['current_question_index']
        return

    question_text = QUESTIONS[current_index]["question"]
    await update.message.reply_text(question_text)

    # Запускаем таймер
    if context.user_data.get('timer_task'):
        context.user_data['timer_task'].cancel()

    context.user_data['is_awaiting_answer'] = True
    context.user_data['timer_task'] = asyncio.create_task(
        async_timer(update, context)
    )

# Асинхронная функция таймера
async def async_timer(update, context):
    try:
        await asyncio.sleep(15)
        
        if context.user_data.get('is_awaiting_answer'):
            await update.message.reply_text("Время вышло! ⏰ Ответ не засчитан.")
            context.user_data['is_awaiting_answer'] = False
            context.user_data['current_question_index'] += 1
            await send_next_question(update, context)
            
    except asyncio.CancelledError:
        pass

# Обработчик ответов пользователя
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'current_question_index' not in context.user_data or not context.user_data.get('is_awaiting_answer'):
        await update.message.reply_text("Чтобы начать викторину, отправь команду /start.")
        return

    # Останавливаем таймер
    if context.user_data.get('timer_task'):
        context.user_data['timer_task'].cancel()
        del context.user_data['timer_task']

    current_index = context.user_data['current_question_index']
    
    correct_answer = QUESTIONS[current_index]["answer"].lower()
    user_answer = update.message.text.strip().lower()

    if user_answer == correct_answer:
        context.user_data['score'] += 1
        await update.message.reply_text("Правильно! 🎉")
    else:
        await update.message.reply_text(f"Неправильно. Правильный ответ: {correct_answer.capitalize()} 😢")

    # Переходим к следующему вопросу
    context.user_data['is_awaiting_answer'] = False
    context.user_data['current_question_index'] += 1
    await send_next_question(update, context)
    
def main():
    print("Бот викторины запущен...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_quiz))
    app.add_handler(CommandHandler("stop", stop_quiz))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))
    
    app.run_polling()

if __name__ == "__main__":
    main()