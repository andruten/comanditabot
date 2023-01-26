import logging
import os

from dotenv import load_dotenv
from telegram.ext.dispatcher import Dispatcher
from telegram.ext.updater import Updater

from chat_statistics import ChatStatisticsMessageHandlerFactory
from commands import (MiMiMiCommandHandler, PunisherCommandHandler,
                      StarCommandHandler, WeatherInKoreaCommandHandler)
from reactions import ReactionHandlerFactory

load_dotenv()

LOG_LEVEL = logging.DEBUG if os.environ.get('LOG_LEVEL', 'INFO') == 'DEBUG' else logging.INFO
logging.basicConfig(level=LOG_LEVEL,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def main():
    updater = Updater(
        os.environ.get('BOT_TOKEN'),
        use_context=True,
    )
    dispatcher: Dispatcher = updater.dispatcher
    # Commands
    dispatcher.add_handler(MiMiMiCommandHandler())
    dispatcher.add_handler(PunisherCommandHandler())
    dispatcher.add_handler(StarCommandHandler())
    dispatcher.add_handler(WeatherInKoreaCommandHandler())

    # Messages
    dispatcher.add_handler(ReactionHandlerFactory())
    dispatcher.add_handler(ChatStatisticsMessageHandlerFactory(), group=1)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
