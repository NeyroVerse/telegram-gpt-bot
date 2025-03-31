import os
import openai
import gspread
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()

# Инициализация OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Настройка Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(os.getenv("SPREADSHEET_URL")).sheet1
data = sheet.get_all_records()

# Поиск по таблице
def search_table(parsed):
    result = []
    for row in data:
        if parsed["type"] == "speaker" and parsed["value"].lower() in row["Пользователь"].lower():
            result.append(row)
        if parsed["type"] == "topic" and parsed["value"].lower() in row["Тема выступления"].lower():
            result.append(row)
    return result[:5]

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    gpt_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "user",
            "content": f'Пользователь написал: "{user_input}". Что он хочет: имя спикера или тему? Ответь JSON: {{"type": "speaker/topic", "value": "..."}}'
        }]
    )
    try:
        parsed = eval(gpt_response.choices[0].message.content)
    except:
        await update.message.reply_text("🤖 Не удалось разобрать запрос.")
        return

    results = search_table(parsed)
    if results:
        for row in results:
            msg = f"🎤 *{row['Пользователь']}*
🗂️ {row['Тема выступления']}
📎 {row['Ссылка на базу знаний']}"
            await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text("😕 Ничего не найдено.")

def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Бот запущен на Render")
    app.run_polling()

if __name__ == "__main__":
    main()
