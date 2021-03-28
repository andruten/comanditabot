import re
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.updater import Updater
from telegram.ext.dispatcher import Dispatcher
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.bot import Bot

updater = Updater(
    "1536716016:AAGDdwMXhDQoxia_9FaR0d-buchH8j8z9c0",
    use_context=True,
)

dispatcher: Dispatcher = updater.dispatcher


def mimimi(update: Update, context: CallbackContext):
    response = re.sub('[aeou]', 'i', update.message.reply_to_message.text, flags=re.I)
    response = re.sub('[AEOU]', 'I', response, flags=re.I)
    response = re.sub('[áéóú]', 'í', response, flags=re.I)
    response = re.sub('[ÁÉÓÚ]', 'Í', response, flags=re.I)
    response = re.sub('[àèòù]', 'ì', response, flags=re.I)
    response = re.sub('[ÀÈÒÙ]', 'Ì', response, flags=re.I)
    response = re.sub('[äëöü]', 'ï', response, flags=re.I)
    response = re.sub('[ÄËÖÜ]', 'Ï', response, flags=re.I)

    bot: Bot = context.bot

    bot.send_message(
        chat_id=update.effective_chat.id,
        text=response,
    )


def sentenciador(update: Update, context: CallbackContext):
    bot: Bot = context.bot
    bot.send_message(
        chat_id=update.effective_chat.id,
        text="Esto tiene, por lo menos, 3 días.",
    )


def star(update: Update, context: CallbackContext):
    bot: Bot = context.bot
    bot.send_message(
        chat_id=update.message.from_user.id,
        text=update.message.reply_to_message.text,
    )


dispatcher.add_handler(CommandHandler("mimimi", mimimi))
dispatcher.add_handler(CommandHandler("sentenciador", sentenciador))
dispatcher.add_handler(CommandHandler("star", star))
updater.start_polling()
