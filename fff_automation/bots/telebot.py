from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters, Dispatcher
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, ReplyKeyboardMarkup, ChatAction, Bot
from telegram.ext.dispatcher import run_async
from telegram.ext.updater import JobQueue
from queue import Queue  # in python 2 it should be "from Queue"
from threading import Thread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from functools import wraps
from telegram.utils.helpers import mention_html
import sys
import traceback
import json
import logging
import os
import pickle
from fff_automation.modules import settings
from fff_automation.modules import utils
from fff_automation.modules import database
from fff_automation.classes.group import Group
from fff_automation.classes.call import Call

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("telegram.bot")

# GLOBAL VARIABLES - CALL CONVERSATION
CALL_DETAILS, EDIT_CALL, EDIT_ARGUMENT, ADD_TITLE, ADD_DATE, ADD_TIME = range(
    6)

# GLOBAL VARIABLES - GROUP CONVERSATION
GROUP_INFO, EDIT_GROUP, CATEGORY, REGION, RESTRICTION, IS_SUBGROUP, PARENT_GROUP, PURPOSE, MANDATE, ONBOARDING = range(
    10)

# GLOBAL VARIABLES - DELETE GROUP CONVERSATION
CANCEL_DELETE_GROUP, CONFIRM_DELETE_GROUP, DOUBLE_CONFIRM_DELETE_GROUP = range(
    3)

TIMEOUT = -2


# CALL CONVERSATION MESSAGES TEXT
save_group_message = "<b>TRANSPARENCY BOT</b> \nThank you for adding me to this chat! I am the FFF Transparency Bot and I'm managed by the [WG] Transparency! \nI can help your group by keeping track of planned calls.\nPlease follow this wizard to complete saving this group's informations in the database:\n\n<b>Select a Category for this group:</b>"
save_group_alreadyregistered_message = "<b>TRANSPARENCY BOT</b>\nThis group has already been registered once, no need to do it again\nType /help tp get a list of available commands"
new_group_description = "- /newgroup -> This command is run automatically once the bot is added to a groupchat. It will get some information about the group (such as group Title and admins) and save it onto the FFF Database.\n<code>/newgroup</code>"
new_call_description = "- /newcall -> Schedule a call in the FFF Database as well as in the Transparency Calendar and Trello Board. \nArguments: <b>Title, Date, Time (GMT), Duration (optional), Description (optional), Agenda Link (optional):</b> \n<code>/newcall Group Call, Wednesday 15th March, 15:00, 00:45, Checkup Call, Link</code>"
help_description = "<b>BOT INFORMATION</b>\nThe FFF Transparency Bot can respond to the following commands:\n - /help -> Get a list of all available commands\n{}\n\n<b>The following commands are automatically run by the bot:</b>\n{}"
new_call_onlygroups_message = "This bot command  only works in groupchats! \nIn order for this command to work, please add me to the group you are trying to schedule the call for. \nKindest regards, \nFFF Transparency Bot"
chat_not_registerred = "<b>This group is not yet registerred in the database</b> \nTo proceed in registering a new call for this group, please make sure the group is first registered in the database.\n\n<b>To register a call in the database, use the command:</b>\n\n {}\n\nFor any technical problems, contact @davidwickerhf"
input_argument_text = "<b>SCHEDULE A NEW CALL</b>\nFollow this wizard to schedule a new call!\n\nPlease reply to this message with the <b>{}</b> for the call you are registering\n\n[Step X out of X]"
wrong_time_text = "<b>WARNING</b>\nThe Time you submitted is not recognized. Please submit a time for the call again with the following format:\n<code>hours:minutes | 15:00</code>\nAlso note that the time you input will be treated as GMT"
wrong_date_text = "<b>WARNING</b>\nThe Date you submitted is not recognized. Please submit a date for the call again with the following format:\n<code>day/month/year | 15/03/2019</code>"
text_input_argument = "<b>SCHEDULE A NEW CALL - ADD A {}</b>\nFollow this wizard to schedule a new call!\n\nPlease reply to this message with the <b>{}</b> for the call you are registering"
cancel_add_call_text = "<b>CALL SCHEDULING CANCELLED</b>\nThe call hasn't been scheduled"


def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context, *args, **kwargs)

    return command_func


def help(update, context):
    update.message.chat.send_message(text=help_description.format(
        new_call_description, new_group_description), parse_mode=ParseMode.HTML)


######################## GROUP CONVERSATION FUNCTIONS #######################

def new_group(update, context):
    for user in update.message.new_chat_members:
        if user.username == "WGtransparencybot":
            print("BOT: --- BOT ADDED IN GROUP ---")
            # LAUNCH SAVE GROUP DEF
            save_group(update, context)


@run_async
def save_group(update, context):
    print("BOT: --- SAVE GROUP INFO ---")
    # GET GROUP INFORMATION
    chat = update.message.chat
    title = chat.title
    chat_id = chat.id
    user_id = update.message.from_user.id
    if chat_id == user_id:
        print("Chat is user")
        update.message.chat.send_message(
            text="This command can be run only in group chats")
        return ConversationHandler.END
    elif (database.find_row_by_id("groups", chat_id)[0] == -1):
        admins = chat.get_administrators()

        # SAVE GROUP INSTANCE IN PICKLE
        group = Group(chat_id=chat_id, title=title, admins=admins,
                      platform="Telegram", user_id=user_id, message=update.message)

        # CREATE MARKUP FOR CATEOGORY CHOICE:
        markup = group_menu(
            [database.trelloc.WORKING_GROUP, database.trelloc.DISCUSSION_GROUP, database.trelloc.PROJECT], [database.trelloc.WORKING_GROUP, database.trelloc.DISCUSSION_GROUP, database.trelloc.PROJECT])

        # SEND MESSAGE WITH INTRO AND REQUEST OF CATEGORY
        group.message = chat.send_message(
            text=save_group_message, parse_mode=ParseMode.HTML, reply_markup=markup)
        utils.dump_pkl('newgroup', group)
        return CATEGORY
    else:
        print("Group is already registered")
        chat.send_message(
            text=save_group_alreadyregistered_message, parse_mode=ParseMode.HTML)
        return ConversationHandler.END


def group_info(update, context):
    print("BOT: --- GROUP INFO ---")


def edit_group(update, context):
    print("BOT: --- EDIT GROUP INFO ---")


@run_async
def category(update, context):
    print("BOT: --- CATEGORY ---")
    query = update.callback_query
    user_id = update.callback_query.from_user.id
    chat_id = update.effective_chat.id
    print("TELEBOT: CATEGORY: Chat Instance: ", chat_id)
    query.answer()

    if utils.load_pkl('newgroup', chat_id, user_id) == "":
        print("TELEBOT: ERROR - Persistence file not found")
        return CATEGORY

    # LOAD PERSISTENCE FILE
    group = utils.load_pkl('newgroup', chat_id, user_id)
    if user_id != group.user_id:
        return CATEGORY
    else:
        group.category = query.data

    # SET NEW TEXT AND MARKAP FOR LEVEL REQUEST
    text = "Ok, cool!\nNow please select the <b>region</b> this group concerns: "
    markup = group_menu(["Africa", "Asia", "North America", "South America", "Oceania", "Europe", "Global"], [
        database.trelloc.regions['Africa'],
        database.trelloc.regions['Asia'],
        database.trelloc.regions['North America'],
        database.trelloc.regions['South America'],
        database.trelloc.regions['Oceania'],
        database.trelloc.regions['Europe'],
        database.trelloc.regions['Global']], 2)
    print("BOT - CATEGORY: Created Region Markup")
    # EDIT MESSAGE TEXT AND MARKUP -  REQUEST REGION
    query.edit_message_text(text, parse_mode=ParseMode.HTML)
    query.edit_message_reply_markup(markup)
    group.message = query.message
    utils.dump_pkl('newgroup', group)
    return REGION


@run_async
def region(update, context):
    print("BOT: --- REGION ---")
    query = update.callback_query
    user_id = update.callback_query.from_user.id
    chat_id = update.effective_chat.id
    query.answer()

    if utils.load_pkl('newgroup', chat_id, user_id) == "":
        print("TELEBOT: ERROR - Persistence file not found")
        return REGION

    # LOAD PERSISTENCE FILE
    group = utils.load_pkl('newgroup', chat_id, user_id)
    if user_id != group.user_id:
        return REGION
    else:
        group.region = utils.getKeysByValue(
            database.trelloc.regions, query.data)[0]

    # SET NEW TEXT AND MARKAP FOR RESTRICTION REQUEST
    text = "Cool! Next, please select the <b>access level</b> for this this group: \n\n<b>Open</b> - Any fff activist working on the international level is allowed to enter\n\n<b>Restricted</b> - Some level of restriction (example: n. activists per country/region\n\n<b>Closed</b> - The group is closed"
    markup = group_menu(["Open", "Restricted", "Closed"],
                        [database.trelloc.restrictions['Open'],
                         database.trelloc.restrictions['Restricted'],
                         database.trelloc.restrictions['Closed']])
    query.edit_message_text(text, parse_mode=ParseMode.HTML)
    query.edit_message_reply_markup(markup)
    group.message = query.message
    utils.dump_pkl('newgroup', group)
    return RESTRICTION


@run_async
def restriction(update, context):
    print("BOT: --- RESTRICTION ---")
    query = update.callback_query
    user_id = update.callback_query.from_user.id
    chat_id = update.effective_chat.id
    query.answer()

    if utils.load_pkl('newgroup', chat_id, user_id) == "":
        print("TELEBOT: ERROR - Persistence file not found")
        return RESTRICTION

    # LOAD PERSISTENCE FILE
    group = utils.load_pkl('newgroup', chat_id, user_id)
    if user_id != group.user_id:
        return RESTRICTION
    else:
        group.restriction = utils.getKeysByValue(
            database.trelloc.restrictions, query.data)[0]

    # SET NEW TEXT AND MARKAP FOR IS SUBGOUP REQUEST
    text = "Awesome. Is this chat a sub-group of any working/discussion group in fridays for future? Answer by clicking the buttons below:"
    markup = group_menu(["No", "Yes"], [0, 1])
    query.edit_message_text(text, parse_mode=ParseMode.HTML)
    query.edit_message_reply_markup(markup)
    group.message = query.message
    utils.dump_pkl('newgroup', group)
    return IS_SUBGROUP


@run_async
def is_subgroup(update, context):
    print("BOT: --- IS SUBGROUP ---")
    query = update.callback_query
    user_id = update.callback_query.from_user.id
    chat_id = update.effective_chat.id
    query.answer()

    if utils.load_pkl('newgroup', chat_id, user_id) == "":
        print("TELEBOT: ERROR - Persistence file not found")
        return IS_SUBGROUP

    # LOAD PERSISTENCE FILE
    group = utils.load_pkl('newgroup', chat_id, user_id)
    if user_id != group.user_id:
        return IS_SUBGROUP

    print("BOT - IS SUBGROUP: Query:", query.data, " type: ", type(query.data))
    if query.data == str(1):
        print("BOT: Select parents")
        group.is_subgroup = True

        # SET NEW TEXT AND MARKAP FOR PARENT REQUEST
        if len(database.get_all_rows()) > 0:
            print("BOT: Groups found")
            text = "Alright, select below the parent group of this group chat:"
            markup = subgroup_menu(
                group=group, direction=1)
            query.edit_message_text(text)
            query.edit_message_reply_markup(markup)
            group.message = query.message
            utils.dump_pkl('newgroup', group)
            return PARENT_GROUP
        else:
            print("BOT: No groups available for parents")
            text = "Mmh... It seams no other group has been registerred yet... To add a parent to a group, make sure you register that group chat first!"
            markup = group_menu(["Next"], [0])
            query.edit_message_text(text, parse_mode=ParseMode.HTML)
            query.edit_message_reply_markup(markup)
            group.message = query.message
            utils.dump_pkl('newgroup', group)
            return IS_SUBGROUP
    elif query.data == str(0):
        print("BOT: No parents")
        group.is_subgroup = False

        # SET NEW TEXT AND MARKAP FOR PURPOSE REQUEST
        text = "Alright, last two steps! Please reply to this message with a short description of the purpose and mandate of the group.\nYou can skip this step by clicking the button below."
        markup = group_menu(["Skip"], ["skip"])
        query.edit_message_text(text, parse_mode=ParseMode.HTML)
        query.edit_message_reply_markup(markup)
        group.message = query.message
        utils.dump_pkl('newgroup', group)
        return PURPOSE


@run_async
def parent_group(update, context):
    print("BOT: --- PARENT GROUP ---")
    query = update.callback_query
    user_id = update.callback_query.from_user.id
    chat_id = update.effective_chat.id
    query.answer()

    if utils.load_pkl('newgroup', chat_id, user_id) == "":
        print("TELEBOT: ERROR - Persistence file not found")
        return PARENT_GROUP

    # LOAD PERSISTENCE FILE
    group = utils.load_pkl('newgroup', chat_id, user_id)
    if user_id != group.user_id:
        return PARENT_GROUP

    if query.data in (0, 1):
        markup = subgroup_menu(
            group=group, direction=query.data)
        query.edit_message_reply_markup(markup)
        group.message = query.message
        utils.dump_pkl('newgroup', group)
        return PARENT_GROUP
    else:
        print("TELEBOT: parent_group(): Query Data: ", query.data)
        group.parentgroup = query.data

        # SET NEW TEXT AND MARKAP FOR PURPOSE REQUEST
        text = "Great! Last two steps! Please reply to this message with a short description of the purpose and mandate of the group.\nYou can skip this step by clicking the button below."
        markup = group_menu(["Skip"], ["skip"])
        query.edit_message_text(text, parse_mode=ParseMode.HTML)
        query.edit_message_reply_markup(markup)
        group.message = query.message
        utils.dump_pkl('newgroup', group)
        return PURPOSE


@run_async
def purpose(update, context):
    print("BOT: --- PURPOSE ---")
    try:
        # UPDATE IS MESSAGE
        user_id = update.message.from_user.id
        chat_id = update.message.chat.id
    except:
        # UPDATE IS QUERY
        user_id = update.callback_query.from_user.id
        chat_id = update.effective_chat.id

    if utils.load_pkl('newgroup', chat_id, user_id) == "":
        print("TELEBOT: ERROR - Persistence file not found")
        return PURPOSE
    # LOAD PERSISTENCE FILE
    group = utils.load_pkl('newgroup', chat_id, user_id)
    if user_id != group.user_id:
        return PURPOSE

    try:
        query = update.callback_query
        query.answer()
        text = "Alright, we'll skip that. Last question:\nPlease reply to this message with a description of who is allowed access to this group and how can activists join this group. You can skip this step as well with the button below."
        markup = group_menu(["Skip"], ["skip"])
        query.edit_message_text(text, parse_mode=ParseMode.HTML)
        query.edit_message_reply_markup(markup)
        group.message = query.message
        utils.dump_pkl('newgroup', group)
        return ONBOARDING
    except:
        print("BOT: User sent messages")
        group.purpose = update.message.text
        # SET NEW TEXT AND MARKAP FOR PURPOSE REQUEST
        text = "Great! Last step!\nPlease reply to this message with a description of who is allowed access to this group and how can activists join this group. You can skip this step as well with the button below."
        markup = group_menu(["Skip"], ["skip"])
        group.message.edit_text(
            text=text, parse_mode=ParseMode.HTML, reply_markup=markup)
        utils.dump_pkl('newgroup', group)
        return ONBOARDING


@run_async
@send_typing_action
def onboarding(update, context):
    print("BOT: --- ONBOARDING ---")
    try:
        # UPDATE IS MESSAGE
        user_id = update.message.from_user.id
        chat_id = update.message.chat.id
    except:
        # UPDATE IS QUERY
        user_id = update.callback_query.from_user.id
        chat_id = update.effective_chat.id

    if utils.load_pkl('newgroup', chat_id, user_id) == "":
        print("TELEBOT: ERROR - Persistence file not found")
        return REGION

    # LOAD PERSISTENCE FILE
    group = utils.load_pkl('newgroup', chat_id, user_id)
    if user_id != group.user_id:
        return REGION

    try:
        group.onboarding = update.message.text
        group.message.delete()
        group.message = update.message.reply_text(
            'Alright, this group is being registered... this might take a minute...')
        save_group_info(update.message.chat, group)
        group.message.delete()
        return ConversationHandler.END
    except:
        query = update.callback_query
        query.answer()
        query.edit_message_text(
            'Alright, this group is being registered... this might take a minute...')
        save_group_info(group.message.chat, group)
        query.message.delete()
        return ConversationHandler.END


# GROUP UTILS ----------------------------------------

def group_menu(button_titles, callbacks, cols=1):
    print("BOT: group_menu()")
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


def subgroup_menu(group, direction, size=4):
    values = database.rotate_groups(
        first_index=group.pgroup_last_index, direction=direction, size=size)
    print("TELEBOT: Rotated Groups: ", values)
    rotated_groups = values[0]
    print("Check 1 ", rotated_groups)
    group.pgroup_last_index = values[1]
    utils.dump_pkl('newgroup', group)
    keyboard = []
    for group in rotated_groups:
        print("Check 2")
        row = []
        group_id = group[0]
        print("TELEBOT: subgroup_menu(): Group Id: ", group_id)
        title = database.get_group_title(group_id)
        button = InlineKeyboardButton(text=title, callback_data=group_id)
        row.append(button)
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="<=", callback_data=0),
                     InlineKeyboardButton(text="=>", callback_data=1)])
    markup = InlineKeyboardMarkup(keyboard)
    return markup


def save_group_info(chat, group):
    # GROUP SAVING: Chat id, Title, Admins, Category, Region, Restrictions, is_subgroup,  parentgroup, purpose, onboarding
    print("SAVE GROUP INFO -----------------------------")
    group.date = datetime.utcnow()
    card_url = database.save_group(group)
    if card_url == -1:
        chat.send_message(
            text="There was a problem in adding the call to the database.\nPlease contact @davidwickerhf for technical support.")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton("Trello Card", url=str(
        card_url)), InlineKeyboardButton("Edit Info", callback_data="EDIT_GROUP")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    print("BOT - Save Group Info: Made Kayboard")

    text = "<b>{}</b> has been saved in the database!".format(group.title)
    utils.delete_pkl('newgroup', group.chat_id, group.user_id)

    chat.send_message(
        text=text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    print("BOT - Save Group Info: Sent Reply")
####################### DELETE GROUP FUNCTIONS ##############################


@run_async
def delete_group(update, context):
    print("BOT: --- DELETE GROUP ---")
    user = update.message.from_user
    chat_id = update.message.chat.id

    member = update.message.chat.get_member(update.message.from_user.id)
    print("BOT: Member Status: ", member.status)
    if chat_id == user.id:
        print("Chat is user")
        update.message.chat.send_message(
            text="This command can be run only in group chats")
        return ConversationHandler.END
    elif database.find_row_by_id(item_id=chat_id)[0] == -1:
        print("BOT - Delete Group: Group is not registerred")
        update.message.reply_text(
            text="This group isn't registerred yet, thus it can't be deleted. Please register this group with the following command:\n/newgroup - This command will take you through a wizard to register this group's information into the FFF Transparency Database.")
        return ConversationHandler.END
    elif member.status == "creator":
        print("BOT - Delete Group: Command was sent by owner/admin")
        markup = group_menu(['NO!', 'Yes, delete the group'], [0, 1])
        message = update.message.reply_text(
            text="<b>WARNING</b>\nBy deleting a group, it's information will be erased from the database and from the Trello Board. All tied calls events will be deleted from both the Trello Board and Google Calendar. Be aware that this action cannot be undone. Use /archivegroup if you are simply archiving the group.\n\nAre you sure you want to delete this group permanently?", reply_markup=markup, parse_mode=ParseMode.HTML)

        # ADD GROUP TO PERSISTANCE
        group = Group(chat_id, update.message.chat.title, update.message.chat.get_administrators(
        ), 'Telegram', user.id, message)
        utils.dump_pkl('deletegroup', group)
        return CONFIRM_DELETE_GROUP
    else:
        owner_username = ""
        for admin in update.message.chat.get_administrators():
            if admin.status == "creator":
                owner_username = admin.user.username
        print("BOT - Delete Group: User does not have permission to delete the group")
        update.message.reply_text(
            text="Sorry, you don't have permission to delete this group. Please ask the group owner to do it.\n@{}".format(owner_username))
        utils.delete_pkl('deletegroup', chat_id, user.id)
        return ConversationHandler.END


@run_async
def confirm_delete_group(update, context):
    print("BOT: --- CONFIRM DELETE GROUP ---")
    query = update.callback_query
    chat_id = update.effective_chat.id
    user_id = query.from_user.id
    group = utils.load_pkl('deletegroup', chat_id, user_id)
    if group == "" or group.user_id != user_id:
        # USER DOES NOT HAVE PERMISSION TO DELETE BOT
        return CONFIRM_DELETE_GROUP
    else:
        query.answer()
        print("BOT: Query Data: ", query.data, " Type: ", type(query.data))

        if query.data == str(0):
            # USER CLICKED DO NOT DELETE BUTTON
            text = "Alright, the group will not be deleted."
            query.edit_message_text(text, parse_mode=ParseMode.HTML)
            utils.delete_pkl('deletegroup', chat_id, user_id)
            return ConversationHandler.END
        elif query.data == str(1):
            # USER CLICKED DELETE BUTTON
            markup = group_menu(['No, don\'t', 'Yes, delete it'], [0, 1])
            text = "Are you really, really sure you want to permanently delete this group's information?"
            query.edit_message_text(text=text, reply_markup=markup)
            group.message = query.message
            utils.dump_pkl('deletegroup', group)
            return DOUBLE_CONFIRM_DELETE_GROUP
        print("BOT: Error in Query data in Confirm Delete Group")


@run_async
@send_typing_action
def double_confirm_delete_group(update, context):
    print("BOT: --- DOUBLE CONFIRM DELETE GROUP ---")
    chat_id = update.effective_chat.id
    user_id = update.callback_query.from_user.id
    group = utils.load_pkl('deletegroup', chat_id, user_id)
    if group == "" or group.user_id != user_id:
        # USER DOES NOT HAVE PERMISSION TO DELETE BOT
        return DOUBLE_CONFIRM_DELETE_GROUP
    else:
        query = update.callback_query
        query.answer()
        if query.data == str(0):
            # USER CLICKED DO NOT DELETE BUTTON
            text = "Alright, the group will not be deleted."
            query.edit_message_text(text=text)
            # DELETE PERSISTENCE FILE
            utils.delete_pkl('deletegroup', chat_id, user_id)
            return ConversationHandler.END
        elif query.data == str(1):
            # USER CLICKED DELETE BUTTON
            text = "Ok, this group is being deleted... This might take a minute..."
            query.edit_message_text(text=text)
            database.delete_group(chat_id, user_id)
            text = "@{} Cool, this group's information has been deleted from the database, as well as the Trello Board. All call events have been erased.".format(
                query.from_user.username)
            query.edit_message_text(text=text)
            # DELETE PERSISTENCE FILE
            utils.delete_pkl('deletegroup', chat_id, user_id)
            return ConversationHandler.END
####################### CALL CONVERSATION FUNCTIONS #########################


@run_async
@send_typing_action
def new_call(update, context):
    message = update.message
    message_id = message.message_id
    groupchat = update.message.chat
    user = message.from_user
    user_id = user.id
    chat_id = groupchat.id
    message_id = message.message_id
    username = user['username']
    full_name = "{} {}".format(user['first_name'], user['last_name'])
    print("Got chat id")

    if groupchat.id == user.id:
        print("Chat is user")
        groupchat.send_message(
            text=new_call_onlygroups_message)
        return ConversationHandler.END
    elif database.find_row_by_id(item_id=update.message.chat.id)[0] == -1:
        print("Chat is not registered yet")
        text = chat_not_registerred.format(
            new_group_description)
        groupchat.send_message(
            text=text, parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    else:
        message_text = update.message.text + ' '
        print("Message Text: " + message_text)
        command = message_text[:message_text.find(' ') + 1]
        print(command)
        # ALGORITHM IS NOT WORKING - AND IS SLOW
        propcall = Call(chat_id=chat_id, user_id=user_id,
                        message_id=message_id, username="@{}".format(username), message=message)
        call = utils.format_string(message_text, command, propcall)

        # ARGUMENTS FORMAT: TITLE, DATE, TIME, DURATION, DESCRIPTION, AGENDA LINK, LINK
        print("GET ARGUMENTS")
        if call.title == '':
            print("Requesting Title input")
            # SEND MESSAGE
            format_input_argument(update, 0, call.TITLE, call)
            return ADD_TITLE
        elif call.date == '':
            print("Title is not missing - Requesting Date input")
            # SEND MESSAGE
            format_input_argument(update, 0, call.DATE, call)
            return ADD_DATE
        elif call.time == '':
            print("Date is not missing - Requesting Time input")
            # SEND MESSAGE
            format_input_argument(update, 0, call.TIME, call)
            return ADD_TIME

        print("Not returned get arguments -> ALL necessary arguments are alraedy given")
        # SAVE CALL TO DATABASE

        save_call_info(update, context, call)
        return ConversationHandler.END


def call_details(update, context):
    print("CALL DETAILS")


def edit_call(update, context):
    print("EDIT CALL")


def edit_argument(update, context):
    print("EDIT ARGUMENT")


@run_async
@send_typing_action
def add_title(update, context):
    print("ADD CALL TITLE")
    # GET CALL SAVED IN PERSISTANCE FILE
    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    call = utils.load_pkl('newcall', chat_id, user_id)
    if call == "" or user_id != call.user_id:
        return ADD_TITLE

    call.title = update.message.text

    # Request Call Date Input
    if call.date == '':
        format_input_argument(update, 1, call.DATE, call)
        return ADD_DATE
    elif call.time == '':
        format_input_argument(update, 1, call.TIME, call)
        return ADD_TIME
    else:
        print("CONVERSATION END - send call details")
        # SAVE INFO IN DATABASE
        save_call_info(update, context, call)
        return ConversationHandler.END


@run_async
@send_typing_action
def add_date(update, context):
    # GET CALL SAVED IN PERSISTANCE FILE
    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    call = utils.load_pkl('newcall', chat_id, user_id)
    if call == "" or user_id != call.user_id:
        return ADD_DATE

    print("ADD CALL DATE")
    print("Requesting user input")
    date_text = update.message.text
    print("Date Text: " + date_text)
    if utils.str2date(date_text) != -1:
        # INPUT IS CORRECT
        call.date = utils.str2date(date_text)
        print("Date is valid: ", call.date)
    else:
        # INPUT IS INCORRECT
        keyboard = [[InlineKeyboardButton("Cancel", callback_data="cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        call.message.delete()
        call.message = update.message.reply_text(
            text=wrong_date_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        utils.dump_pkl('newcall', call)
        return ADD_DATE

    if call.time == '':
        format_input_argument(update, 1, call.TIME, call)
        print("Going to next step")
        return ADD_TIME
    else:
        print("CONVERSATION END - send call details")
        # SAVE INFO IN DATABASE
        save_call_info(update, context, call)
        return ConversationHandler.END


@run_async
@send_typing_action
def add_time(update, context):
    # GET CALL SAVED IN PERSISTANCE FILE
    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    call = utils.load_pkl('newcall', chat_id, user_id)
    if call == "" or user_id != call.user_id:
        return ADD_TIME

    print("ADD TIME")
    print("Requesting user input")
    message_text = update.message.text
    if utils.str2time(message_text) != -1:
        # INPUT IS CORRECT
        call.time = utils.str2time(message_text)
        print("Inputted time: ", str(call.time))
        print("CONVERSATION END - send call details")
        # SAVE INFO IN DATABASE
        save_call_info(update, context, call)
        return ConversationHandler.END
    else:
        # INPUT IS INCORRECT
        keyboard = [[InlineKeyboardButton("Cancel", callback_data="cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        call.message.delete()
        call.message = update.message.reply_text(
            text=wrong_time_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        utils.dump_pkl('newcall', call)
        return ADD_TIME


@run_async
@send_typing_action
def cancel_call(update, context):
    # GET CALL SAVED IN PERSISTANCE FILE
    chat_id = update.effective_chat.id
    user_id = update.callback_query.from_user.id
    call = utils.load_pkl('newcall', chat_id, user_id)
    update.callback_query.answer()
    if call == "" or user_id != call.user_id:
        return
    else:
        print("CANCEL PRESSED")
        call.message.edit_text(
            text=cancel_add_call_text, parse_mode=ParseMode.HTML)
        utils.delete_pkl('newcall', chat_id, user_id)
    return ConversationHandler.END


def format_input_argument(update, state, key, call):
    keyboard = [[InlineKeyboardButton(
        "Cancel", callback_data="cancel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    argument_title = call.order.get(key)

    if state == 0:
        print("SEND FIRST GET ARGUMENTS MESSAGE")
        # Code runs for the first time -> Send message
        call.message = update.message.reply_text(text=text_input_argument.format(
            argument_title.upper(), argument_title), parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    else:
        # Code already run -> edit message
        call.message.delete()
        call.message = update.message.reply_text(text=text_input_argument.format(
            argument_title.upper(), argument_title), parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        print("EDIT GET ARGUMENTS MESSAGE")
    utils.dump_pkl('newcall', call)


@send_typing_action
def save_call_info(update, context, call):
    call.message.delete()
    username = update.message.from_user.username
    message = update.message.chat.send_message(
        text="Saving call information... This might take a minute...")

    values = database.save_call(call)
    if values == -1:
        message.edit_text(
            text="There was a problem in adding the call to the database.\nPlease contact @davidwickerhf for technical support.")
        return ConversationHandler.END

    calendar_url = values[0]
    trello_url = values[1]

    keyboard = [[InlineKeyboardButton("Calendar", url=str(
        calendar_url)), InlineKeyboardButton("Trello Card", url=str(trello_url))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    print("Made Kayboard")

    text = utils.format_call_info("save_call", call)
    print("Formatted text")
    utils.delete_pkl('newcall', call.chat_id, call.user_id)

    message.delete()
    update.message.reply_text(
        text=text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    print("Sent Reply")


def error(update, context):
    logger.warning('BOT: Update caused error: "%s"', context.error)
    # add all the dev user_ids in this list. You can also add ids of channels or groups.
    # MAKE THIS A ENV VARIABLE------------------------------------------------------------------------------------------
    devs = [427293622]
    # we want to notify the user of this problem. This will always work, but not notify users if the update is an
    # callback or inline query, or a poll update. In case you want this, keep in mind that sending the message
    # could fail
    if update.effective_message:
        text = "Hey. I'm sorry to inform you that an error happened while running your command..." \
               "My developer will be notified immediatly."
        update.effective_message.reply_text(text)
    # This traceback is created with accessing the traceback object from the sys.exc_info, which is returned as the
    # third value of the returned tuple. Then we use the traceback.format_tb to get the traceback as a string, which
    # for a weird reason separates the line breaks in a list, but keeps the linebreaks itself. So just joining an
    # empty string works fine.
    trace = "".join(traceback.format_tb(sys.exc_info()[2]))
    # lets try to get as much information from the telegram update as possible
    payload = ""
    # normally, we always have an user. If not, its either a channel or a poll update.
    if update.effective_user:
        payload += f' with the user {mention_html(update.effective_user.id, update.effective_user.first_name)}'
    # there are more situations when you don't get a chat
    if update.effective_chat:
        payload += f' within the chat <i>{update.effective_chat.title}</i>'
        if update.effective_chat.username:
            payload += f' (@{update.effective_chat.username})'
    # but only one where you have an empty payload by now: A poll (buuuh)
    if update.poll:
        payload += f' with the poll id {update.poll.id}.'
    # lets put this in a "well" formatted text
    text = f"Hey.\n The error <code>{context.error}</code> happened{payload}. The full traceback:\n\n<code>{trace}" \
           f"</code>"
    # and send it to the dev(s)
    for dev_id in devs:
        context.bot.send_message(dev_id, text, parse_mode=ParseMode.HTML)
    # we raise the error again, so the logger module catches it. If you don't use the logger module, use it.
    raise


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


def setup(token):
    bot = Bot(token)
    update_queue = Queue()
    job_queue = JobQueue()
    dp = Dispatcher(bot=bot, update_queue=update_queue,
                    use_context=True, job_queue=job_queue)
    job_queue.set_dispatcher(dp)

    # Commands
    dp.add_handler(CommandHandler("help", help))
    group_handler = ConversationHandler(
        entry_points=[MessageHandler(
            Filters.status_update.new_chat_members, new_group), CommandHandler("newgroup", save_group)],
        states={
            GROUP_INFO: [],
            EDIT_GROUP: [],
            CATEGORY: [CallbackQueryHandler(category)],
            REGION: [CallbackQueryHandler(region)],
            RESTRICTION: [CallbackQueryHandler(restriction)],
            IS_SUBGROUP: [CallbackQueryHandler(is_subgroup)],
            PARENT_GROUP: [CallbackQueryHandler(parent_group)],
            PURPOSE: [MessageHandler(Filters.text, purpose), CallbackQueryHandler(purpose)],
            ONBOARDING: [MessageHandler(Filters.text, onboarding), CallbackQueryHandler(onboarding)],
            TIMEOUT: [MessageHandler(Filters.all, callback=conv_timeout)],
        },
        fallbacks=[],
        conversation_timeout=timedelta(seconds=240),
    )
    call_handler = ConversationHandler(
        entry_points=[CommandHandler(
            'newcall', new_call), CommandHandler('editcall', edit_call)],
        states={
            CALL_DETAILS: [CallbackQueryHandler(edit_call, pattern='^' + str(EDIT_CALL) + '$')],
            EDIT_CALL: [],
            EDIT_ARGUMENT: [],
            ADD_TITLE: [MessageHandler(Filters.text, add_title), CallbackQueryHandler(cancel_call)],
            ADD_DATE: [MessageHandler(Filters.text, add_date), CallbackQueryHandler(cancel_call)],
            ADD_TIME: [MessageHandler(Filters.text, add_time), CallbackQueryHandler(cancel_call)],
            TIMEOUT: [MessageHandler(Filters.all, callback=conv_timeout)],
        },
        fallbacks=[CallbackQueryHandler(cancel_call)],
        conversation_timeout=timedelta(seconds=240),
    )
    delete_group_handler = ConversationHandler(
        entry_points=[CommandHandler('deletegroup', delete_group)],
        states={
            CONFIRM_DELETE_GROUP: [CallbackQueryHandler(confirm_delete_group)],
            DOUBLE_CONFIRM_DELETE_GROUP: [
                CallbackQueryHandler(double_confirm_delete_group)],
            TIMEOUT: [MessageHandler(Filters.all, callback=conv_timeout)]
        },
        fallbacks=[],
        conversation_timeout=timedelta(seconds=240),
    )
    dp.add_handler(call_handler)
    dp.add_handler(group_handler)
    dp.add_handler(delete_group_handler)
    dp.add_error_handler(error)

    thread = Thread(target=dp.start, name='dispatcher')
    thread.start()

    return update_queue
