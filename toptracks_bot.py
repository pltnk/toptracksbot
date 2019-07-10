import fetching
import logging
import re

from telegram import ChatAction
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater

# from telegram import InlineQueryResultArticle, InputTextMessageContent
# from telegram.ext import InlineQueryHandler


TOKEN = f'{fetching.bot_api}'
REQUEST_KWARGS = {
    'proxy_url': 'socks5://orbtl.s5.opennetwork.cc:999',
    # Optional, if you need authentication:
    'urllib3_proxy_kwargs': {
        'username': '147578754',
        'password': 'cTv8N72n',
    }
}

updater = Updater(token=TOKEN, use_context=True, request_kwargs=REQUEST_KWARGS)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def start(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="Enter an artist or a band name.")


def send_top(update, context):
    logging.info(f'(send_top) Incoming message: args={context.args}, text="{update.message.text}"')
    if update.message.text.startswith('/three '):
        number = 3
    elif update.message.text.startswith('/ten '):
        number = 10
    else:
        number = 5
    keyphrase = ' '.join(context.args) if context.args else update.message.text
    if re.compile(r'^/(three|five|ten)\s*$').search(keyphrase):
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text=f'Command must be followed by artist name.\nExample: {keyphrase.strip()} Nirvana')
    else:
        context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
        top = create_top(keyphrase, number)
        for track in top:
            context.bot.send_message(chat_id=update.message.chat_id, text=f'youtube.com/watch?v={track}')


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
    message = 'Enter an artist or a band name to get their top tracks of all time ' \
              'according to last.fm charts.\nBy default this bot sends top five tracks.' \
              '\n/three <artist> - get top three\n/five <artist> - get top five' \
              '\n/ten <artist> - get top ten\n/info <artist> - get short bio of an artist\n/help - show this message.'
    context.bot.send_message(chat_id=update.message.chat_id, text=message)


def unknown(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text='Unknown command, try /help.')


def create_top(keyphrase, number=5):
    try:
        playlist = fetching.get_playlist_api(keyphrase, number)
    except Exception as e:
        logging.warning(e)
        logging.info('Creating playlist without API')
        playlist = fetching.get_playlist(keyphrase, number)
    try:
        ids = fetching.fetch_ids_api(playlist)
    except Exception as e:
        logging.warning(e)
        logging.info('Fetching YouTube ids without API')
        ids = fetching.fetch_ids(playlist)
    return ids


start_handler = CommandHandler('start', start)
default_handler = MessageHandler(Filters.text, send_top)
top_handler = CommandHandler(['three', 'five', 'ten'], send_top)
info_handler = CommandHandler('info', send_info)
# inline_caps_handler = InlineQueryHandler(inline_caps)
help_handler = CommandHandler('help', send_help)
unknown_handler = MessageHandler(Filters.command, unknown)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(default_handler)
dispatcher.add_handler(top_handler)
dispatcher.add_handler(info_handler)
# dispatcher.add_handler(inline_caps_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(unknown_handler)

try:
    logging.info('Starting bot...')
    updater.start_polling()
    updater.idle()
except Exception as e:
    logging.error(f'Unable to start a bot. {e}')

