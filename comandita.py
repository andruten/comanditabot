import logging
import os

from dotenv import load_dotenv
from telegram.ext.updater import Updater
from telegram.ext.dispatcher import Dispatcher

from commands import (
    MiMiMiCommandHandler,
    PunisherCommandHandler,
    StarCommandHandler,
    WeatherInKoreaCommandHandler,
    TranscriberCommandHandler,
)
from handlers import (
    MessageHandlerFactory,
    AudioHandlerFactory,
)

load_dotenv()

LOG_LEVEL = logging.DEBUG if os.environ.get("LOG_LEVEL", "INFO") == "DEBUG" else logging.INFO
logging.basicConfig(level=LOG_LEVEL,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def main():
    updater = Updater(
        os.environ.get("BOT_TOKEN"),
        use_context=True,
    )
    dispatcher: Dispatcher = updater.dispatcher
    dispatcher.add_handler(MiMiMiCommandHandler())
    dispatcher.add_handler(PunisherCommandHandler())
    dispatcher.add_handler(StarCommandHandler())
    dispatcher.add_handler(WeatherInKoreaCommandHandler())
    dispatcher.add_handler(TranscriberCommandHandler())

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandlerFactory())
    dispatcher.add_handler(AudioHandlerFactory())

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
