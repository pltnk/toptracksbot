import fetching
import logging
import os
import storing

from telegram import ChatAction
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater

# from telegram import InlineQueryResultArticle, InputTextMessageContent
# from telegram.ext import InlineQueryHandler

TOKEN = os.getenv('BOT_TOKEN')
MODE = os.getenv('BOT_MODE')
PORT = int(os.environ.get('PORT', '8443'))
HEROKU_APP = os.getenv('HEROKU_APP')

# proxy settings
# REQUEST_KWARGS = {
#     'proxy_url': 'socks5://orbtl.s5.opennetwork.cc:999',
#     # Optional, if you need authentication:
#     'urllib3_proxy_kwargs': {
#         'username': '147578754',
#         'password': 'cTv8N72n',
#     }
# }
# REQUEST_KWARGS = {'proxy_url': 'socks5://94.130.73.31:8118'}

# updater that uses proxy
# updater = Updater(token=TOKEN, use_context=True, request_kwargs=REQUEST_KWARGS)

updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def start(update, context):
    logging.info(f'(start) Incoming message: args={context.args}, text="{update.message.text}"')
    context.bot.send_message(chat_id=update.message.chat_id, text="Enter an artist or a band name.")


def send_top(update, context):
    logging.info(f'(send_top) Incoming message: args={context.args}, text="{update.message.text}"')
    keyphrase = update.message.text
    context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    try:
        top = storing.process(keyphrase)
        for youtube_id in top:
            context.bot.send_message(chat_id=update.message.chat_id, text=f'youtube.com/watch?v={youtube_id}')
    except Exception as e:
        logging.error(e)
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text=f'An error occurred, try /help.'
                                      f'\nMost likely it was impossible to find this artist on last.fm, '
                                      f'make sure this name is correct.')


def send_info(update, context):
    logging.info(f'(send_info) Incoming message: args={context.args}, text="{update.message.text}"')
    if len(context.args) == 0:
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text=f'Command must be followed by artist name.\nExample: /info Nirvana')
    else:
        keyphrase = ' '.join(context.args)
        context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
        info = fetching.get_info(keyphrase)
        context.bot.send_message(chat_id=update.message.chat_id, text=info)


def send_help(update, context):
    logging.info(f'(send_help) Incoming message: args={context.args}, text="{update.message.text}"')
    message = 'Enter an artist or a band name to get their top three tracks of all time ' \
              'according to last.fm charts.\n/info <artist> - get short bio of an artist\n/help - show this message.'
    context.bot.send_message(chat_id=update.message.chat_id, text=message)


def unknown(update, context):
    logging.info(f'(unknown) Incoming message: args={context.args}, text="{update.message.text}"')
    context.bot.send_message(chat_id=update.message.chat_id, text='Unknown command, try /help.')


start_handler = CommandHandler('start', start)
default_handler = MessageHandler(Filters.text, send_top)
info_handler = CommandHandler('info', send_info)
# inline_handler = InlineQueryHandler(inline_top)
help_handler = CommandHandler('help', send_help)
unknown_handler = MessageHandler(Filters.command, unknown)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(default_handler)
dispatcher.add_handler(info_handler)
# dispatcher.add_handler(inline_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(unknown_handler)


def main():
    try:
        if MODE == 'prod':
            updater.start_webhook(listen="0.0.0.0",
                                  port=PORT,
                                  url_path=TOKEN)
            updater.bot.set_webhook(f"https://{HEROKU_APP}.herokuapp.com/{TOKEN}")
        else:
            logging.info('Starting bot')
            updater.start_polling()
            updater.idle()
    except Exception as e:
        logging.error(f'Unable to start a bot. {e}')


if __name__ == '__main__':
    main()
