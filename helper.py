from typing import Union
from pydantic import BaseModel
import httpx
import logging

logger = logging.getLogger(__name__)

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
