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
    response = re.sub('[aeiou]', 'i', update.message.reply_to_message.text, flags=re.I)
    response = re.sub('[AEIOU]', 'I', response, flags=re.I)
    response = re.sub('[áéíóú]', 'í', response, flags=re.I)
    response = re.sub('[ÁÉÍÓÚ]', 'Í', response, flags=re.I)
    response = re.sub('[àèìòù]', 'ì', response, flags=re.I)
    response = re.sub('[ÀÈÌÒÙ]', 'Ì', response, flags=re.I)
    response = re.sub('[äëïöü]', 'ï', response, flags=re.I)
    response = re.sub('[ÄËÏÖÜ]', 'Ï', response, flags=re.I)

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


dispatcher.add_handler(CommandHandler("mimimi", mimimi))
dispatcher.add_handler(CommandHandler("sentenciador", sentenciador))
updater.start_polling()

