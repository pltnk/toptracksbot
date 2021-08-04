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
from telegram.ext.filters import Filters

from bot import fetching, storing
from bot.exceptions import PlaylistRetrievalError, VideoIDsRetrievalError


BOT_TOKEN = os.environ["TTBOT_TOKEN"]
BOT_MODE = os.getenv("TTBOT_MODE", "dev")
WEBHOOK_PORT = int(os.getenv("TTBOT_WEBHOOK_PORT", "8443"))
HEROKU_APP = os.getenv("TTBOT_HEROKU_APP", "")

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("bot")
logger.setLevel(logging.DEBUG)


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
    except PlaylistRetrievalError as e:
        logger.error(e)
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"An error occurred, most likely I couldn't find this artist on Last.fm."
            f"\nMake sure this name is correct.",
        )
    except VideoIDsRetrievalError as e:
        logger.error(e)
        context.bot.send_message(
            chat_id=update.message.chat_id, text=f"Unable to get videos from YouTube."
        )
    except Exception as e:
        logger.exception(e)
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"Unexpected error, feel free to open an issue on GitHub: "
            f"github.com/pltnk/toptracksbot/issues/new",
        )
    else:
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
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # initialize handlers
    top_handler = MessageHandler(
        Filters.text & (~Filters.command), send_top, run_async=True
    )
    info_handler = CommandHandler(["info", "i"], send_info, run_async=True)
    help_handler = CommandHandler(["help", "h", "start"], send_help, run_async=True)
    unknown_handler = MessageHandler(Filters.command, unknown, run_async=True)

    # add handlers to dispatcher
    dispatcher.add_handler(top_handler)
    dispatcher.add_handler(info_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(unknown_handler)

    # start bot
    try:
        if BOT_MODE == "prod":
            updater.start_webhook(
                listen="127.0.0.1", port=WEBHOOK_PORT, url_path=BOT_TOKEN
            )
            updater.bot.set_webhook(f"https://{HEROKU_APP}.herokuapp.com/{BOT_TOKEN}")
        else:
            logger.info("Starting bot")
            updater.start_polling()
            updater.idle()
    except Exception as e:
        logger.exception(f"Unable to start a bot. {e}")


if __name__ == "__main__":
    main()
