from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters, Dispatcher
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, ReplyKeyboardMarkup, ChatAction, Bot
from telegram.ext.dispatcher import run_async
from telegram.ext.updater import JobQueue
from queue import Queue  # in python 2 it should be "from Queue"
from threading import Thread
from datetime import datetime, timedelta
from functools import wraps
from telegram.utils.helpers import mention_html
from tzlocal import get_localzone
import sys
import traceback
import json
import logging
import os
import html
import pickle
import pytz

from movement_assistant.modules import settings, utils, database, interface
from movement_assistant.modules import utils
from movement_assistant.modules import database
from movement_assistant.classes.group import Group
from movement_assistant.classes.call import Call
from movement_assistant.classes.botupdate import BotUpdate
from movement_assistant.classes.feedback import Feedback
from movement_assistant.bots.telebot.texts import *
from movement_assistant.modules.settings import *


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("telegram.bot")
# GLOBAL VARIABLES - CONVERSATION
TIMEOUT = -2


def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context, *args, **kwargs)

    return command_func


####################### GROUP UTILS ----------------------------------------
def subgroup_menu(botupdate: BotUpdate, direction, size=4, method='newgroup'):
    obj = botupdate.obj
    values = interface.rotate_objs(
        first_index=botupdate.pobj_last_index, direction=direction, size=size)
    print("TELEBOT: Rotated Groups: ", values)
    rotated_groups = values[0]
    print("Check 1 ", rotated_groups)
    botupdate.pobj_last_index = values[1]
    utils.dump_pkl(method, botupdate)
    children_ids = []
    for child in obj.children:
        if child != None:
            children_ids.append(child.id)
    keyboard = []
    for pgroup in rotated_groups:
        if pgroup.id != obj.id and pgroup.id not in children_ids:
            row = []
            group_id = pgroup.id
            print("TELEBOT: subgroup_menu(): Group Id: ", group_id)
            title = pgroup.title
            button = InlineKeyboardButton(text=title, callback_data=group_id)
            row.append(button)
            keyboard.append(row)

    if method == 'newgroup':
        keyboard.append([InlineKeyboardButton('No Parent Group', callback_data='no_parent')])

    keyboard.append([InlineKeyboardButton(text="<=", callback_data=LEFT),
                     InlineKeyboardButton(text="=>", callback_data=RIGHT)])
    
    if method == 'edit_group':
        keyboard.append([InlineKeyboardButton('Cancel', callback_data='cancel')])
    markup = InlineKeyboardMarkup(keyboard)
    return markup


def rotate_calls(botupdate: BotUpdate, direction):
    if botupdate.obj_selection == GROUP_CALLS:
        id = botupdate.update.effective_chat.id
    else:
        id = ''
    values = interface.rotate_objs(
        first_index=botupdate.pobj_last_index,
        direction=direction,
        id=id,
        table='calls',
        field='chat_id'
    )
    rotated_objs = values[0]
    botupdate.pobj_last_index = values[1]
    keyboard = []
    for obj in rotated_objs:
        row = []
        print("TELEBOT: rotate_calls(): Obj Id: ", obj.id)
        button = InlineKeyboardButton(text=obj.title, callback_data=obj.id)
        row.append(button)
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="<=", callback_data=LEFT),
                     InlineKeyboardButton(text="=>", callback_data=RIGHT)])
    markup = InlineKeyboardMarkup(keyboard)
    return markup


def format_group_info(botupdate, type=0, error_text=''):
    group = botupdate.obj
    print('TELEBOT: format_group_info()')
    if type == 0:
        text = '<b>{}</b> has been saved in the database!'.format(group.title)
    elif type == 1:
        text = edited_group_text
    elif type == 2:
        text = error_text
    elif type == 3:
        text = group_info_text.format(group.title)
    text = text +  '''\n<b>Category:</b> {}\n<b>Restriction:</b> {}\n<b>Region:</b> {}\n<b>Color:</b> {}\n<b>Purpose:</b> {}\n<b>Onboarding:</b> {}'''.format(
        group.category, group.restriction, group.region, group.get_color(), group.purpose, group.onboarding)
    if group.is_subgroup:
        text = text + \
            '\n<b>Parent Group:</b> {}'.format(
                database.get_group_title(group.parentgroup))
    return text


def format_group_buttons(group):
    card_url = 'https://trello.com/c/{}'.format(group.card_id)
    keyboard = [[InlineKeyboardButton("Trello Card", url=str(card_url)), InlineKeyboardButton("Edit Info", callback_data='edit_group')]]
    markup = InlineKeyboardMarkup(keyboard)
    return markup
    
################################### UTIlS ############
def create_menu(button_titles, callbacks, cols=1):
    print("BOT: menu()")
    keyboard = []
    index = 0
    row = []
    for title in button_titles:
        keyboard_button = InlineKeyboardButton(
            title, callback_data=callbacks[index])
        if len(row) < cols:
            row.append(keyboard_button)
        else:
            keyboard.append(row)
            row = []
            row.append(keyboard_button)
        index += 1
    if row != "":
        keyboard.append(row)
    markup = InlineKeyboardMarkup(keyboard)
    return markup


def error(update, context):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb = ''.join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    message = (
        'An exception was raised while handling an update\n'
        '<pre>update = {}</pre>\n\n'
        '<pre>context.chat_data = {}</pre>\n\n'
        '<pre>context.user_data = {}</pre>\n\n'
        '<pre>{}</pre>'
    ).format(
        html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(str(context.chat_data)),
        html.escape(str(context.user_data)),
        html.escape(tb)
    )

    # Finally, send the message
    devs = settings.get_var('DEVS')
    for dev in devs:
        context.bot.send_message(chat_id=dev, text=message, parse_mode=ParseMode.HTML)


def conv_timeout(update, context):
    try:
        user_id = update.callback_query.from_user.id
        chat_id = update.effective_chat.id
    except:
        user_id = update.message.from_user.inde
        chat_id = update.effective_chat.id
    obj = None

    try:
        obj = utils.delete_pkl('newgroup', chat_id, user_id)
    except:
        try:
            obj = utils.delete_pkl('deletegroup', chat_id, user_id)
        except:
            try:
                obj = utils.delete_pkl('newcall', chat_id, user_id)
            except:
                print("TELEBOT: No conv pkl found")

    if obj != None:
        obj.message.edit_text(
            "Conversation Timeout - to complete the action, please run the command again.")