import logging
import os

from dotenv import load_dotenv
from telegram.ext import Application

from chat_statistics import ChatStatisticsMessageHandlerFactory
from commands import MiMiMiCommandHandler, PunisherCommandHandler, StarCommandHandler, WeatherInKoreaCommandHandler
from commands.chat_statistics import ChatStatisticsCommandHandler
from reactions import ReactionHandlerFactory

load_dotenv()

LOG_LEVEL = logging.DEBUG if os.environ.get('LOG_LEVEL', 'INFO') == 'DEBUG' else logging.INFO
logging.basicConfig(level=LOG_LEVEL,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def main():
    application = Application.builder().token(os.environ.get('BOT_TOKEN')).build()
    # Commands
    application.add_handler(MiMiMiCommandHandler())
    application.add_handler(PunisherCommandHandler())
    application.add_handler(StarCommandHandler())
    application.add_handler(WeatherInKoreaCommandHandler())
    application.add_handler(ChatStatisticsCommandHandler())

    # Messages
    application.add_handler(ReactionHandlerFactory())
    application.add_handler(ChatStatisticsMessageHandlerFactory(), group=1)

    application.run_polling()


if __name__ == '__main__':
    main()
