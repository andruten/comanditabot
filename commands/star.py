from telegram import Update, Bot
from telegram.error import Unauthorized
from telegram.ext import CallbackContext

from commands.base import BaseCommandHandler


class StarCommandHandler(BaseCommandHandler):
    COMMAND_NAME = "star"

    def process(self, update: Update, context: CallbackContext):
        bot: Bot = context.bot
        try:
            bot.send_message(
                chat_id=update.message.from_user.id,
                text=update.message.reply_to_message.text,
            )
        except Unauthorized:
            bot.send_message(
                chat_id=update.effective_chat.id,
                text="Antes de poder enviarte mensajes "
                     "tienes que iniciar una conversación "
                     "conmigo en https://t.me/comandita_bot",
            )
        except AttributeError:
            bot.send_message(
                chat_id=update.effective_chat.id,
                text="Cita un mensaje que quieras guardar ⭐️",
            )
