import logging
import os

from dotenv import load_dotenv
from telegram.ext import Application

from chat_statistics import ChatStatisticsMessageHandlerFactory
from commands import MiMiMiCommandHandler, PunisherCommandHandler, StarCommandHandler, WeatherInKoreaCommandHandler
from commands.chat_statistics import ChatStatisticsCommandHandler
from reactions import ReactionHandlerFactory

load_dotenv()

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
app_log_level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO'), logging.INFO)
logging.getLogger("chat_statistics").setLevel(app_log_level)
logging.getLogger("clients").setLevel(app_log_level)
logging.getLogger("commands").setLevel(app_log_level)
logging.getLogger("reactions").setLevel(app_log_level)
logger = logging.getLogger(__name__)


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

    logger.info('Bot started...')


if __name__ == '__main__':
    main()
