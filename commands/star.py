from telegram import Bot, Update
from telegram.error import Forbidden
from telegram.ext import CallbackContext

from commands.base import BaseCommandHandler


class StarCommandHandler(BaseCommandHandler):
    COMMAND_NAME = 'star'

    async def process(self, update: Update, context: CallbackContext):
        bot: Bot = context.bot
        try:
            await bot.send_message(
                chat_id=update.message.from_user.id,
                text=update.message.reply_to_message.text,
            )
        except Forbidden:
            await bot.send_message(
                chat_id=update.effective_chat.id,
                text='Antes de poder enviarte mensajes '
                     'tienes que iniciar una conversación '
                     'conmigo en https://t.me/comandita_bot',
            )
        except AttributeError:
            await bot.send_message(
                chat_id=update.effective_chat.id,
                text='Cita un mensaje que quieras guardar ⭐️',
            )
