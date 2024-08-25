from datetime import datetime
from telegram import Update

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


def give_time(full=False):
    """Returns a string containing the time, and date + time if full = True."""
    if full:
        now = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    else:
        now = datetime.now().strftime("%H:%M")
    return now

def print_input(update:Update) -> str:
    """Takes the user input and prints in the command line the message."""
    if update.message.text:
        user_name = update.message.from_user.name
        user_id = update.message.from_user.id # TODO: Save all new pairs of (name, id)

        print(f"{give_time(full = True)} | {update.message.chat.title} | {update.message.from_user.name} | {update.message.from_user.id} | {update.message.text}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    print_input(update)
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    print_input(update)
    user = update.effective_user
    await update.message.reply_html(
        rf"I am afraid I have no ability to help you."
    )