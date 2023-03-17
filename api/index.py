import logging
from telegram import Update, Poll, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext, PollHandler, PollAnswerHandler, Dispatcher, MessageHandler, Filters
from deta import Deta
import random
from typing import Union
from pydantic import BaseModel
import httpx
import logging
from fastapi import FastAPI
import time
import os

logger = logging.getLogger(__name__)

TOKEN = os.environ.get('TOKEN')
app = FastAPI()
deta = Deta("d011wxuu1l1_ZDghSFpyhLyrzvzE6AArrRSnnjNwHEeW")
quiz_user = deta.Base("quiz_user")

WELCOME_MESSAGE = '''Welcome <a href="tg://user?id={user_id}">{user_name}</a> to Quiz/Motivational Bot

To use this bot 
    - send /quiz to get a random quiz
    - send /motivation to get a random motivational quote

By default, the bot will send you a quiz and a motivational quote every day at 8:00 AM UTC.


For more info send /help
'''

QUIZ_URL = "https://opentdb.com/api.php?amount=1&category=9&difficulty=easy&type=multiple"
QUIZ_URL = 'https://the-trivia-api.com/api/questions?limit=1'

MOTIVATIONAL_URL = 'https://zenquotes.io/api/quotes'


def get_quiz():
    '''
    This will get a random quiz from the API
    '''
    try:
        response = httpx.get(QUIZ_URL)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(e)


def get_motivational():
    '''
    This will get a random motivational quote from the API
    '''
    try:
        response = httpx.get(MOTIVATIONAL_URL)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(e)


class TelegramWebhook(BaseModel):
    update_id: int
    message: Union[dict, None] = None
    edited_message: Union[dict, None] = None
    channel_post: Union[dict, None] = None
    edited_channel_post: Union[dict, None] = None
    inline_query: Union[dict, None] = None
    chosen_inline_result: Union[dict, None] = None
    callback_query: Union[dict, None] = None
    shipping_query: Union[dict, None] = None
    pre_checkout_query: Union[dict, None] = None
    poll: Union[dict, None] = None
    poll_answer: Union[dict, None] = None
    my_chat_member: Union[dict, None] = None
    chat_member: Union[dict, None] = None
    chat_join_request: Union[dict, None] = None

    def to_json(self):
        '''
        Returns a JSON representation of the model
        '''
        data = {}
        for key, value in self.__dict__.items():
            if key.startswith('_'):
                continue
            if value is None:
                continue
            data[key] = value

        return data


def waiter_wrapper(func):
    def wrapper(update: Update, context: CallbackContext):
        try:
            user = update.effective_user or update.message.from_user
            msg = context.bot.send_message(
                chat_id=user.id,
                text="Please wait...",
            )
            func(update, context)
            context.bot.delete_message(
                chat_id=user.id,
                message_id=msg.message_id
            )
        except Exception as e:
            logger.error('Error happened in a Wrapper %s', e)
    return wrapper


@waiter_wrapper
def start(update: Update, context: CallbackContext):
    update.message.reply_html(WELCOME_MESSAGE.format(
        user_id=update.message.from_user.id, user_name=update.message.from_user.first_name))
    user = update.message.from_user.to_dict()
    user['key'] = str(user.get('id') or user.get('user_id'))
    if not quiz_user.get(user['key']):
        quiz_user.put(user)


@waiter_wrapper
def start_quiz(update: Update, context: CallbackContext):
    logger.info('Quiz started')
    quiz = get_quiz()
    options = []
    options.append(quiz[0]['correctAnswer'])
    for option in quiz[0]['incorrectAnswers']:
        options.append(option)

    random.shuffle(options)
    correct = options.index(quiz[0]['correctAnswer'])
    user = update.effective_user or update.message.from_user
    context.bot.send_poll(
        chat_id=user.id,
        question=quiz[0]['question'],
        type=Poll.QUIZ,
        allows_multiple_answers=False,
        options=options,
        correct_option_id=correct,
        protect_content=True,
        is_anonymous=False,
        # TODO: add timer
    )
    return 0


@waiter_wrapper
def start_motivation(update: Update, context: CallbackContext):
    logger.info('Motivation started')
    motivation = get_motivational()
    quote = random.choice(motivation)
    user = update.effective_user or update.message.from_user
    context.bot.send_message(
        chat_id=user.id,
        text=quote['q'] + '\n\n' + quote['a'],
    )
    return 0


@waiter_wrapper
def help(update: Update, context: CallbackContext):
    update.message.reply_text(WELCOME_MESSAGE.format(
        user_id=update.message.from_user.id, user_name=update.message.from_user.first_name), parse_mode='HTML')


@waiter_wrapper
def stats(update: Update, context: CallbackContext):
    res = quiz_user.fetch()
    all_items = res.items
    while res.last:
        res = quiz_user.fetch(last=res.last)
        all_items += res.items

    text += 'Total users: {}\n\n'.format(len(all_items))
    update.message.reply_text(text)


def register_dispatcher(dispatcher: Dispatcher):
    dispatcher.add_handler(PollAnswerHandler(start_quiz))
    dispatcher.add_handler(PollHandler(start_quiz))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("quiz", start_quiz))
    dispatcher.add_handler(CommandHandler("motivation", start_motivation))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("stats", stats))
    dispatcher.add_handler(MessageHandler(Filters.text, start))


def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # register dispatcher
    register_dispatcher(dispatcher)

    updater.start_polling()
    updater.idle()


@app.get("/")
def index():
    return {"message": "Hello World"}


@app.post("/webhook")
def webhook(our_update: TelegramWebhook):
    bot = Bot(TOKEN)
    update = Update.de_json(our_update.to_json(), bot)
    dispatcher = Dispatcher(bot, None)

    register_dispatcher(dispatcher)

    dispatcher.process_update(update)
    return {"message": "ok"}


@app.get('/api/cron')
def send_motivation():
    users = quiz_user.fetch()
    all_users = users.items
    while users.last:
        users = quiz_user.fetch(last=users.last)
        all_users += users.items

    motivation = get_motivational()

    bot = Bot(TOKEN)
    count = 0
    for user in all_users:
        try:

            rand_motivation = random.choice(motivation)
            bot.send_message(
                chat_id=int(user['key']),
                text=rand_motivation['q'],
            )
            count += 1
            if count == 30:
                time.sleep(1)
                count = 0

        except:
            pass

    return {"message": "ok"}

# if __name__ == '__main__':
#     main()
