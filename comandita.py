from telegram.ext.updater import Updater
from telegram.ext.dispatcher import Dispatcher

from commands.mimimi import MiMiMiCommandHandler
from commands.sentenciador import PunisherCommandHandler
from commands.star import StarCommandHandler
from commands.weather_in_korea import WeatherInKoreaCommandHandler


def main():
    updater = Updater(
        "1536716016:AAGDdwMXhDQoxia_9FaR0d-buchH8j8z9c0",
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
