'''
Module: shared_variables
'''
import datetime
from datetime import date


def get_greeting():
    '''Say your Customer Good Morning/Good Afternoon/Good Eveninig'''
    current_time = datetime.datetime.now()
    hour = current_time.hour

    if 5 <= hour < 12:
        return "Good Morning!"
    elif 12 <= hour < 17:
        return "Good Afternoon!"
    elif 17 <= hour < 21:
        return "Good Evening!"
    else:
        return "Welcome!"


def get_today_date():
    '''Returns the date of today'''
    return date.today()
