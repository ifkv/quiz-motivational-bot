from typing import Union
from pydantic import BaseModel
import httpx
import logging

logger = logging.getLogger(__name__)

QUIZ_URL = "https://opentdb.com/api.php?amount=1&category=9&difficulty=easy&type=multiple"
QUIZ_URL = 'https://the-trivia-api.com/api/questions?limit=1'

MOTIVATIONAL_URL = 'https://zenquotes.io/api/quotes'


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
