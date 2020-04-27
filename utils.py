from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
from itertools import permutations
import dateparser
import re
import pytz
from pytimeparse.timeparse import timeparse
import random


def str2date(string):
    "Parse a string into a datetime object."
    try:
        date = dateparser.parse(string).date()
    except:
        return -1

    if str(date) == "1900-01-01":
        print(str(date), " is an Invalid date")
        return -1
    else:
        return datetime.strftime(date, "%Y/%m/%d")


def str2time(string):
    try:
        date = dateparser.parse(string)
        return date.time()
    except:
        return -1


def str2datetime(string):
    try:
        date = dateparser.parse(string)
        return date
    except:
        return -1


def str2duration(string):
    if ':' in string:
        seconds = timeparse(string, granularity='minutes')
        print("Duration: ", seconds)
    else:
        seconds = timeparse(string)
        print("Duration: ", seconds)

    if seconds is not None:
        return seconds
    else:
        print("Duration not valid")
        return -1


def format_call_info(context, title, date, time, duration, description, link):
    header = ""
    if context == "save_call":
        header = "<b>NEW CALL SCHEDULED</b>\n"
    elif context == "update_call":
        header = "<b>CALL DETAILS UPDATED</b>\n"

    print("UTILS: Duration type: ", type(duration))
    seconds = int(duration)
    hours = seconds / 3600
    rest = seconds % 3600
    minutes = rest / 60
    duration_string = str(hours) + " Hours, " + str(minutes) + " Minutes"

    if description == "":
        description = "N/A"
    if link == "":
        link = "N/A"
    text = header + "Call details: \n\n - <b>Title:</b> {}\n - <b>Date:</b> {}\n - <b>Time (GMT):</b> {}\n - <b>Duration:</b> {}\n\n - <b>Description:</b> {}\n - <b>Agenda Link:</b> {}".format(
        title, date, time, duration_string, description, link)
    return text


def format_string(input_message, command):
    print("Unedited message: ", input_message)
    message = input_message.replace(command, '')
    print("Message after replace: ", message)
    message = message.split(',')
    print("Message after split: ", message)
    arguments = ["", "", "", "", "", ""]
    missing_arguments = []
    available_slots = [0, 1, 2, 3, 4, 5]

    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        # domain...
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    # ALGORITHM IS NOT WORKING
    for argument in message:
        argument = argument.strip()
        print(argument)
        if 1 in available_slots and str2date(argument) != -1:
            # ARGUMENT IS DATE
            arguments[1] = argument
            available_slots.remove(1)
            continue
        elif 2 in available_slots and str2time(argument) != -1:
            # ARGUMENT IS TIME
            print("Time: ", str(argument))
            arguments[2] = argument
            available_slots.remove(2)
            continue
        elif 3 in available_slots and str2duration(argument) != -1:
            # ARGUMENT IS DURATION
            arguments[3] = str2duration(argument)
            available_slots.remove(3)
            continue
        elif 5 in available_slots and re.match(regex, argument) is not None:
            # ARGUMENT IS LINK
            arguments[5] = argument
            available_slots.remove(5)
            continue
        elif arguments[0] == "":
            arguments[0] = argument
        elif len(argument) < len(arguments[0]):
            # ARGUMENT IS DESCRIPTION
            description = arguments[0]
            arguments[0] = argument
            arguments[4] = description
        else:
            arguments[4] = argument

    print(arguments)
    index = 0
    for argument in arguments:
        if argument == "":
            if index == 3:
                arguments[3] = "3600"
            elif index == 0 or index == 1 or index == 2:
                missing_arguments.append(index)
                print("Missing Argument: " + str(index))
        index += 1

    return [arguments, missing_arguments]


def get_random_event_color():
    color_id = random.randrange(1, 11)
    return color_id


def getKeysByValue(dictOfElements, valueToFind):
    listOfKeys = list()
    listOfItems = dictOfElements.items()
    for item in listOfItems:
        if item[1] == valueToFind:
            listOfKeys.append(item[0])
    return listOfKeys


def now_time():
    return datetime.now(tz=pytz.utc)

    return datetime
