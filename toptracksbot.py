"""
This module is a part of Top Tracks Bot for Telegram
and is licensed under the MIT License.
Copyright (c) 2019-2021 Kirill Plotnikov
GitHub: https://github.com/pltnk/toptracksbot
"""


import asyncio
import logging
import os

from telegram import ChatAction, Update
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Updater
from telegram.ext.dispatcher import run_async
from telegram.ext.filters import Filters

import fetching
import storing


TOKEN = os.environ["BOT_TOKEN"]
MODE = os.environ["BOT_MODE"]
PORT = int(os.getenv("PORT", "8443"))
HEROKU_APP = os.environ["HEROKU_APP"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger("bot")
logger.setLevel(logging.DEBUG)


@run_async
def send_top(update: Update, context: CallbackContext) -> None:
    """Process incoming message, send top tracks by the given artist or send an error message."""
    logger.info(
        f'(send_top) Incoming message: args={context.args}, text="{update.message.text}"'
    )
    keyphrase = update.message.text
    context.bot.send_chat_action(
        chat_id=update.message.chat_id, action=ChatAction.TYPING
    )
    try:
        top = asyncio.run(storing.process(keyphrase))
        if top:
            for youtube_id in top:
                context.bot.send_message(
                    chat_id=update.message.chat_id,
                    text=f"youtube.com/watch?v={youtube_id}",
                )
        else:
            context.bot.send_message(
                chat_id=update.message.chat_id,
                text=f"I couldn't find videos of {keyphrase} on YouTube.",
            )
    except Exception as e:
        logger.exception(e)
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"An error occurred, most likely I couldn't find this artist on Last.fm."
            f"\nMake sure this name is correct.",
        )


@run_async
def send_info(update: Update, context: CallbackContext) -> None:
    """Process /info command."""
    logger.info(
        f'(send_info) Incoming message: args={context.args}, text="{update.message.text}"'
    )
    if len(context.args) == 0:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"Command must be followed by artist name.\nExample: /info Nirvana",
        )
    else:
        keyphrase = " ".join(context.args)
        context.bot.send_chat_action(
            chat_id=update.message.chat_id, action=ChatAction.TYPING
        )
        info = asyncio.run(fetching.get_info(keyphrase))
        context.bot.send_message(chat_id=update.message.chat_id, text=info)


@run_async
def send_help(update: Update, context: CallbackContext) -> None:
    """Process /help and /start commands."""
    logger.info(
        f'(send_help) Incoming message: args={context.args}, text="{update.message.text}"'
    )
    message = (
        "Enter an artist or a band name to get their top three tracks of all time "
        "according to Last.fm charts.\n"
        "/info <artist> or /i <artist> - get a short bio of an artist\n"
        "/help or /h - show this message.\n\n"
        "This bot is an open source project, check it on GitHub: github.com/pltnk/toptracksbot"
    )
    context.bot.send_message(chat_id=update.message.chat_id, text=message)


@run_async
def unknown(update: Update, context: CallbackContext) -> None:
    """Process any unknown command."""
    logger.info(
        f'(unknown) Incoming message: args={context.args}, text="{update.message.text}"'
    )
    context.bot.send_message(
        chat_id=update.message.chat_id, text="Unknown command, try /help."
    )


def main() -> None:
    # initialize updater
    updater = Updater(token=TOKEN, use_context=True)
    # updater that uses proxy
    # REQUEST_KWARGS = {'proxy_url': 'http://195.189.96.213:3128'}
    # updater = Updater(token=TOKEN, use_context=True, request_kwargs=REQUEST_KWARGS)
    dispatcher = updater.dispatcher

    # initialize handlers
    top_handler = MessageHandler(Filters.text & (~Filters.command), send_top)
    info_handler = CommandHandler(["info", "i"], send_info)
    help_handler = CommandHandler(["help", "h", "start"], send_help)
    unknown_handler = MessageHandler(Filters.command, unknown)

    # add handlers to dispatcher
    dispatcher.add_handler(top_handler)
    dispatcher.add_handler(info_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(unknown_handler)

    # start bot
    try:
        if MODE == "prod":
            updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)
            updater.bot.set_webhook(f"https://{HEROKU_APP}.herokuapp.com/{TOKEN}")
        else:
            logger.info("Starting bot")
            updater.start_polling()
            updater.idle()
    except Exception as e:
        logger.exception(f"Unable to start a bot. {e}")


if __name__ == "__main__":
    main()
