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
)

load_dotenv()


logging.basicConfig(level=logging.DEBUG,
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
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
