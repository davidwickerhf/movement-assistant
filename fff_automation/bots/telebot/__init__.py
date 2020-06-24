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

from fff_automation.modules import settings, utils, database, interface
from fff_automation.modules.settings import CALL_DETAILS, EDIT_CALL, EDIT_ARGUMENT, ADD_TITLE, ADD_DATE, ADD_TIME, GROUP_INFO, EDIT_GROUP, ARGUMENT, INPUT_ARGUMENT, EDIT_IS_SUBGROUP, EDIT_PARENT, CATEGORY, REGION, RESTRICTION, IS_SUBGROUP, PARENT_GROUP, PURPOSE, ONBOARDING, COLOR, CANCEL_DELETE_GROUP, CONFIRM_DELETE_GROUP, DOUBLE_CONFIRM_DELETE_GROUP, FEEDBACK_TYPE, ISSUE_TYPE, INPUT_FEEDBACK
from fff_automation.modules import utils
from fff_automation.modules import database
from fff_automation.classes.group import Group
from fff_automation.classes.call import Call
from fff_automation.classes.feedback import Feedback
from fff_automation.bots.telebot.texts import *


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
def subgroup_menu(group, direction, size=4, method='newgroup'):
    values = interface.rotate_groups(
        first_index=group.pgroup_last_index, direction=direction, size=size)
    print("TELEBOT: Rotated Groups: ", values)
    rotated_groups = values[0]
    print("Check 1 ", rotated_groups)
    group.pgroup_last_index = values[1]
    utils.dump_pkl(method, group)
    children_ids = []
    for child in group.children:
        if child != None:
            children_ids.append(child.id)
    keyboard = []
    for pgroup in rotated_groups:
        if pgroup.id != group.id and pgroup.id not in children_ids:
            row = []
            group_id = pgroup.id
            print("TELEBOT: subgroup_menu(): Group Id: ", group_id)
            title = pgroup.title
            button = InlineKeyboardButton(text=title, callback_data=group_id)
            row.append(button)
            keyboard.append(row)

    if method == 'newgroup':
        keyboard.append([InlineKeyboardButton('No Parent Group', callback_data='no_parent')])

    keyboard.append([InlineKeyboardButton(text="<=", callback_data=0),
                     InlineKeyboardButton(text="=>", callback_data=1)])
    
    if method == 'edit_group':
        keyboard.append([InlineKeyboardButton('Cancel', callback_data='cancel')])
    markup = InlineKeyboardMarkup(keyboard)
    return markup


def format_group_info(group, type=0, error_text=''):
    print('TELEBOT: format_group_info()')
    if type == 0:
        text = '<b>{}</b> has been saved in the database!'.format(group.title)
    elif type == 1:
        text = edited_group_text
    elif type == 2:
        text = error_text
    text = text +  '''\n<b>Category:</b> {}\n<b>Restriction:</b> {}\n<b>Region:</b> {}\n<b>Color:</b> {}\n<b>Purpose:</b> {}\n<b>Onboarding:</b> {}'''.format(
        group.category, group.restriction, group.region, group.get_color(), group.purpose, group.onboarding)
    if group.is_subgroup:
        text = text + \
            '\n<b>Parent Group:</b> {}'.format(
                database.get_group_title(group.parentgroup))
    return text

    
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