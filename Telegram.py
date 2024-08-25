from Utils.settings import get_parameter
from Utils.Communications import print_input, give_time, start, help_command
from Weather.Weather import summarize, string_to_export
from Transport.SBB import export_string_sbb

import logging
import os
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes


# Nobody truly understand this - however, it works.
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Master function to manage user input via Telegram."""

    print_input(update=update)

    if update.message.text.lower() == "time":
        await update.message.reply_text(f"The time is {give_time(full=True)}.")

    if update.message.text.lower() == "wsh":
        await update.message.reply_text(f"Hello ma poule")

    if update.message.text.lower() == "weather":
        id_ = update.message.from_user.id
        weather_code, min_temp, max_temp, precip, precip_total = summarize(id_user=update.message.from_user.id)
        await update.message.reply_text(string_to_export(weather_code, min_temp, max_temp, precip, precip_total))

    if update.message.text.lower() == "transport":
        id = update.message.from_user.id
        try:
            station = get_parameter(id)["STOP"]
            schedule_message = export_string_sbb(station=get_parameter(id)["STOP"], limit=6)
            
        except:
            schedule_message = export_string_sbb(station=get_parameter("STOP_MAIN"), limit=6)

        await update.message.reply_text(schedule_message)
        

def main() -> None:
    """Start the bot."""

    # Clear terminal
    if os.name == "nt":
        os.system("cls")
    elif os.name == "posix":
        os.system("clear")


    # Create the Application and pass it your bot's token.
    application = Application.builder().token(get_parameter("BOT_TOKEN")).build()


    # # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(MessageHandler(filters.TEXT, handle_input))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":

    main()