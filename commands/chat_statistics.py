from telegram import Bot, Update
from telegram.ext import CallbackContext

from chat_statistics.chat_statistics import ChatStatistics
from commands.base import BaseCommandHandler


class ChatStatisticsCommandHandler(BaseCommandHandler):
    COMMAND_NAME = 'stats'

    def process(self, update: Update, context: CallbackContext):
        chat_id = update.effective_chat.id
        chat_statistics = ChatStatistics()
        daily_statistics = chat_statistics.get_daily_statistics(chat_id)
        text = f'Estadísticas de hoy\n' \
               f'Mensajes: {daily_statistics.messages_count}\n'
        if daily_statistics.photos_count:
            text += f'Fotos: {daily_statistics.photos_count}\n'
        if daily_statistics.videos_count:
            text += f'Videos: {daily_statistics.photos_count}\n'
        if daily_statistics.audios_count:
            text += f'Audios: {daily_statistics.audios_count}\n'
        bot: Bot = context.bot
        bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
        )
