import logging.config
import os

from dotenv import load_dotenv
from telegram.ext import Application

from chat_statistics import ChatStatisticsMessageHandlerFactory
from commands import (
    MiMiMiCommandHandler,
    PunisherCommandHandler,
    StarCommandHandler,
    WeatherInKoreaCommandHandler,
)
from commands.chat_statistics import ChatStatisticsCommandHandler
from media_downloads.handler import MediaMessageHandler
from reactions import ReactionHandlerFactory

load_dotenv()

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "chat_statistics": {"level": LOG_LEVEL},
        "clients": {"level": LOG_LEVEL},
        "commands": {"level": LOG_LEVEL},
        "media_downloads": {"level": LOG_LEVEL},
        "reactions": {"level": LOG_LEVEL},
        "telegram": {"level": "WARNING"},
        "httpx": {"level": "WARNING"},
    },
}

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


def configure_handlers(application):
    application.add_handler(MediaMessageHandler(), group=-1)

    # Commands
    application.add_handler(MiMiMiCommandHandler())
    application.add_handler(PunisherCommandHandler())
    application.add_handler(StarCommandHandler())
    application.add_handler(WeatherInKoreaCommandHandler())
    application.add_handler(ChatStatisticsCommandHandler())

    # Messages
    application.add_handler(ReactionHandlerFactory())
    application.add_handler(ChatStatisticsMessageHandlerFactory(), group=1)


def main():
    application = Application.builder().token(os.environ.get("BOT_TOKEN")).build()
    configure_handlers(application)
    application.run_polling()

    logger.info("Bot started...")


if __name__ == "__main__":
    main()
