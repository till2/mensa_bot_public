import re
import asyncio
from telegram import Bot, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackContext, ContextTypes, filters,
    JobQueue
)
from mensa_utils import get_mensa_id, get_canteen_name, is_canteen_closed, get_meals
from ollama_mensa_bot_utils import get_formatted_mensa_meals, classify_meal, setup_llm
from message_classifier import process_user_message, COMMAND_HELP, COMMAND_MENU, COMMAND_MENSA, COMMAND_CHAT, COMMAND_SETTINGS, COMMAND_RESTART
from time_utils import parse_date_query, format_date_for_display
from langchain_ollama import ChatOllama
import time
from datetime import time as dt_time, datetime, date
from telegram.error import TimedOut, NetworkError
from dotenv import load_dotenv
import os

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Default configurations
DEFAULT_MENSA = "Kiepenheuerallee"
user_mensa_prefs = {}  # {user_id: mensa_name}
DAILY_REPORT_TIME = dt_time(9, 0, 0, tzinfo=datetime.now().astimezone().tzinfo)

# Replace LLM configuration with Ollama setup
llm = setup_llm(model="phi3:3.8b", temperature=0.3)
system_prompt = "Du bist ein hilfsbereicher Assistent, der auch Informationen über die Uni-Mensa geben kann. Antworte bitte auf Deutsch."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return
        
    user_id = update.effective_user.id
    await update.message.reply_text(
        "👋 Hi! Ich bin dein Mensa-Bot.\n\n"
        "Ich kann:\n"
        "- Dir das tägliche Mensa-Menü zeigen 🍽️\n"
        "- Dir vegetarische Optionen empfehlen 🥦\n"
        "- Mit dir über verschiedene Themen chatten 💬\n"
        "\nNutze /hilfe für eine Übersicht aller Befehle!"
    )
    user_mensa_prefs[user_id] = DEFAULT_MENSA

async def hilfe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
        
    help_text = (
        "📚 Verfügbare Befehle:\n"
        "/start - Willkommensnachricht\n"
        "/hilfe - Zeigt diese Hilfe an\n"
        "/menu [datum] - Zeigt das heutige Menü (oder für ein bestimmtes Datum)\n"
        "/mensa <standort> - Setzt deine bevorzugte Mensa\n"
        "/chat - Wechselt in den Chat-Modus\n"
        "/einstellungen - Konfiguriert Menü-Einstellungen\n"
        "/neustart - Setzt Konversation und Einstellungen zurück\n\n"
        "📍 Verfügbare Mensen:\n"
        "- Kiepenheuerallee\n"
        "- Griebnitzsee\n\n"
        "💡 Du kannst auch natürliche Sprache verwenden, z.B.:\n"
        "- \"Was gibt es heute zu essen?\"\n"
        "- \"Zeig mir das Menü für morgen\"\n"
        "- \"Wechsle zur Mensa Griebnitzsee\""
    )
    await update.message.reply_text(help_text)

async def set_mensa_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return
        
    user_id = update.effective_user.id
    args = context.args
    
    if not args:
        await update.message.reply_text(
            "Bitte gib einen Mensa-Standort an.\n"
            "Verfügbare Standorte: Kiepenheuerallee, Griebnitzsee"
        )
        return
        
    try:
        get_mensa_id(args[0])
        user_mensa_prefs[user_id] = args[0]
        await update.message.reply_text(f"✅ Deine Standard-Mensa wurde zu {args[0]} geändert")
    except KeyError:
        await update.message.reply_text(
            f"❌ Ungültiger Mensa-Standort: {args[0]}\n"
            "Verfügbare Standorte: Kiepenheuerallee, Griebnitzsee"
        )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return
        
    user_id = update.effective_user.id
    
    # Handle args as a list or a single string
    if context.args:
        if isinstance(context.args, list):
            target_date = " ".join(context.args)
        else:
            target_date = context.args
    else:
        target_date = date.today().strftime("%Y-%m-%d")
    
    try:
        # Try to parse the date if it's not in YYYY-MM-DD format
        if not re.match(r'\d{4}-\d{2}-\d{2}', target_date):
            target_date = parse_date_query(target_date, llm)
        
        mensa_name = user_mensa_prefs.get(user_id, DEFAULT_MENSA)
        response = get_formatted_mensa_meals(mensa_name, target_date, llm)
        
        # Add a friendly date display
        friendly_date = format_date_for_display(target_date)
        response = response.replace(f"am {target_date}", f"am {friendly_date}")
        
        await update.message.reply_text(response)
    except Exception as e:
        await update.message.reply_text(
            f"❌ Fehler beim Abrufen der Mensa-Daten: {str(e)}\n"
            "Bitte versuche es später erneut."
        )

async def daily_mensa_report(context: CallbackContext):
    job = context.job
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    friendly_date = format_date_for_display(today_str)
    
    for user_id, mensa_name in user_mensa_prefs.items():
        try:
            report = get_formatted_mensa_meals(mensa_name, today_str)
            # Replace the date format with a more friendly one
            report = report.replace(f"am {today_str}", f"am {friendly_date}")
            
            await context.bot.send_message(
                user_id,
                f"☀️ Mensa-Bericht für {friendly_date}\n"
                f"📍 Standort: {mensa_name}\n\n"
                f"{report}"
            )
        except Exception as e:
            print(f"Fehler beim Senden des Tagesberichts an {user_id}: {str(e)}")

async def neustart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return
        
    user_id = update.effective_user.id
    user_mensa_prefs[user_id] = DEFAULT_MENSA
    await update.message.reply_text(
        "🔄 Alle Einstellungen wurden zurückgesetzt.\n"
        f"Standard-Mensa ist jetzt: {DEFAULT_MENSA}"
    )

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return
        
    user_id = update.effective_user.id
    mensa_name = user_mensa_prefs.get(user_id, DEFAULT_MENSA)
    
    settings_text = (
        "⚙️ Deine aktuellen Einstellungen:\n\n"
        f"📍 Mensa: {mensa_name}\n\n"
        "Um deine Mensa zu ändern, nutze den Befehl:\n"
        "/mensa <standort>"
    )
    
    await update.message.reply_text(settings_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    message_text = update.message.text
    
    if not update.effective_user:
        return
        
    user_id = update.effective_user.id
    
    # If it's a command, let the command handlers handle it
    if message_text.startswith('/'):
        return
    
    print(f"Chat-Nachricht von {user_id}: {message_text}")
    
    # Process the message to determine intent
    command, args = process_user_message(message_text, llm)
    
    # Handle the command based on the intent
    if command == COMMAND_HELP:
        await hilfe_command(update, context)
    
    elif command == COMMAND_MENU:
        # Create a new context with the extracted args
        new_context = context
        new_context.args = args
        await menu_command(update, new_context)
    
    elif command == COMMAND_MENSA:
        # Create a new context with the extracted args
        new_context = context
        new_context.args = args
        await set_mensa_command(update, new_context)
    
    elif command == COMMAND_SETTINGS:
        await settings_command(update, context)
    
    elif command == COMMAND_RESTART:
        await neustart_command(update, context)
    
    else:  # Default to chat for anything else
        # Use Ollama for general chat
        messages = [
            ("system", system_prompt),
            ("human", message_text)
        ]
        response = llm.invoke(messages).content.strip()
        await update.message.reply_text(response)

def main():
    print("Starte Mensa-Bot...")
    
    # Add retry settings to the application builder
    app = (ApplicationBuilder()
           .token(TELEGRAM_TOKEN)
           .read_timeout(30)
           .write_timeout(30)
           .connect_timeout(30)
           .get_updates_read_timeout(42)
           .concurrent_updates(False)  # Process updates sequentially
           .build())
    
    # Add error handlers
    async def error_handler(update, context):
        print(f"Exception while handling an update: {context.error}")
        
        if isinstance(context.error, TimedOut):
            print("Connection timed out. Will retry automatically.")
        elif isinstance(context.error, NetworkError):
            print("Network error occurred. Check your internet connection.")
        else:
            # Log all other errors
            print(f"Update {update} caused error {context.error}")
    
    app.add_error_handler(error_handler)
    
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hilfe", hilfe_command))
    app.add_handler(CommandHandler("help", hilfe_command))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("mensa", set_mensa_command))
    app.add_handler(CommandHandler("einstellungen", settings_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("neustart", neustart_command))
    app.add_handler(CommandHandler("restart", neustart_command))
    
    # Message handler for all text messages that are not commands
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Job queue setup
    job_queue = app.job_queue
    if job_queue:
        job_queue.run_daily(daily_mensa_report, time=DAILY_REPORT_TIME)
    else:
        print("Warning: Job queue is not available")
    
    # Start polling
    print("Polling...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,  # Ignore any pending updates
        poll_interval=1.0,  # Polling interval in seconds
    )

if __name__ == "__main__":
    try:
        # Add a cleanup mechanism to ensure proper shutdown
        import atexit
        def cleanup():
            print("Shutting down bot...")
        atexit.register(cleanup)
        
        main()
    except Exception as e:
        print(f"Critical error: {e}")
