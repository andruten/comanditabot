from random import choice
from time import sleep

import requests
from telegram.error import Unauthorized
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.updater import Updater
from telegram.ext.dispatcher import Dispatcher
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.bot import Bot

from commands.mimimi import (
    MiMiMiCommandHandler,
)

OPEN_WEATHER_MAP_APP_ID = "1234"


def sentenciador(update: Update, context: CallbackContext):
    bot: Bot = context.bot
    punishments = [
        "Esto tiene, por lo menos, 3 días.",
        "O sea, chao.",
    ]
    bot.send_message(
        chat_id=update.effective_chat.id,
        text=choice(punishments),
    )


def star(update: Update, context: CallbackContext):
    bot: Bot = context.bot
    try:
        bot.send_message(
            chat_id=update.message.from_user.id,
            text=update.message.reply_to_message.text,
        )
    except Unauthorized:
        bot.send_message(
            chat_id=update.effective_chat.id,
            text="Antes de poder enviarte mensajes "
                 "tienes que iniciar una conversación "
                 "conmigo en https://t.me/comandita_bot",
        )
    except AttributeError:
        bot.send_message(
            chat_id=update.effective_chat.id,
            text="Cita un mensaje que quieras guardar ⭐️",
        )


def weather_in_korea(update: Update, context: CallbackContext):
    bot: Bot = context.bot
    bot.send_message(
        chat_id=update.effective_chat.id,
        text="Dormida... 😡"
    )
    sleep(2)
    bot.send_message(
        chat_id=update.effective_chat.id,
        text="No, en serio, ahora te digo."
    )
    sleep(1)
    query = {
        "q": "Seoul",
        "appid": OPEN_WEATHER_MAP_APP_ID,
        "units": "metric",
    }
    response = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params=query,
    )
    weather_data = response.json()
    weather_text = ", ".join([weather.get("main", "") for weather in weather_data.get("weather", [])])
    temperature = weather_data.get("main", {})
    temp = temperature.get("temp", 0)
    feels_like = temperature.get("feels_like", 0)
    temp_min = temperature.get("temp_min", 0)
    temp_max = temperature.get("temp_max", 0)
    bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Weather: {weather_text}\n"
             f"Temp: {temp}ºC\n"
             f"Feels like: {feels_like}ºC\n"
             f"Min: {temp_min}ºC\n"
             f"Max: {temp_max}ºC",
    )


def main():
    updater = Updater(
        "1234:1234",
        use_context=True,
    )
    dispatcher: Dispatcher = updater.dispatcher
    dispatcher.add_handler(MiMiMiCommandHandler())
    dispatcher.add_handler(CommandHandler("sentenciador", sentenciador))
    dispatcher.add_handler(CommandHandler("star", star))
    dispatcher.add_handler(CommandHandler("tiempoencorea", weather_in_korea))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
