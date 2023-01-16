import logging
import os

from dotenv import load_dotenv
from telegram.ext.dispatcher import Dispatcher
from telegram.ext.updater import Updater

from commands import (MiMiMiCommandHandler, PunisherCommandHandler,
                      StarCommandHandler, WeatherInKoreaCommandHandler)
from reactions import MessageHandlerFactory

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
    dispatcher.add_handler(MiMiMiCommandHandler())
    dispatcher.add_handler(PunisherCommandHandler())
    dispatcher.add_handler(StarCommandHandler())
    dispatcher.add_handler(WeatherInKoreaCommandHandler())

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandlerFactory())

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
