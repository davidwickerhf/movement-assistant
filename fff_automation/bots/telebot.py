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
from tzlocal import get_localzone
import sys
import traceback
import json
import logging
import os
import html
import pickle
from fff_automation.modules import settings, utils, database, interface
from fff_automation.modules.settings import CALL_DETAILS, EDIT_CALL, EDIT_ARGUMENT, ADD_TITLE, ADD_DATE, ADD_TIME, GROUP_INFO, EDIT_GROUP, ARGUMENT, INPUT_ARGUMENT, EDIT_IS_SUBGROUP, EDIT_PARENT, CATEGORY, REGION, RESTRICTION, IS_SUBGROUP, PARENT_GROUP, PURPOSE, ONBOARDING, COLOR, CANCEL_DELETE_GROUP, CONFIRM_DELETE_GROUP, DOUBLE_CONFIRM_DELETE_GROUP, FEEDBACK_TYPE, ISSUE_TYPE, INPUT_FEEDBACK
from fff_automation.modules import utils
from fff_automation.modules import database
from fff_automation.classes.group import Group
from fff_automation.classes.call import Call
from fff_automation.classes.feedback import Feedback
import pytz

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("telegram.bot")

# GLOBAL VARIABLES - CONVERSATION
TIMEOUT = -2


# GROUP CONVERSATION MESSAGES TEXT
save_group_message = "<b>TRANSPARENCY BOT</b> \nThank you for adding me to this chat! I am the FFF Transparency Bot and I'm managed by the [WG] Transparency! \nI can help your group by keeping track of planned calls.\nPlease follow this wizard to complete saving this group's informations in the database:\n\n<b>Select a Category for this group:</b>"
save_group_alreadyregistered_message = "<b>TRANSPARENCY BOT</b>\nThis group has already been registered once, no need to do it again\nType /help tp get a list of available commands"
new_group_description = "- /activate -> This command is run automatically once the bot is added to a groupchat. It will get some information about the group (such as group Title and admins) and save it onto the FFF Database.\n<code>/newgroup</code>"
new_call_description = "- /newcall -> Schedule a call in the FFF Database as well as in the Transparency Calendar and Trello Board. \nArguments: <b>Title, Date, Time (GMT), Duration (optional), Description (optional), Agenda Link (optional):</b> \n<code>/newcall Group Call, Wednesday 15th March, 15:00, 00:45, Checkup Call, Link</code>"
help_description = "<b>BOT INFORMATION</b>\nThe FFF Transparency Bot can respond to the following commands:\n - /help -> Get a list of all available commands\n{}\n\n<b>The following commands are automatically run by the bot:</b>\n{}"
new_call_onlygroups_message = "This bot command  only works in groupchats! \nIn order for this command to work, please add me to the group you are trying to schedule the call for. \nKindest regards, \nFFF Transparency Bot"
chat_not_registerred = "<b>This group is not yet registerred in the database</b> \nTo proceed in registering a new call for this group, please make sure the group is first registered in the database.\n\n<b>To register a call in the database, use the command:</b>\n\n {}\n\nFor any technical problems, contact @davidwickerhf"
input_argument_text = "<b>SCHEDULE A NEW CALL</b>\nFollow this wizard to schedule a new call!\n\nPlease reply to this message with the <b>{}</b> for the call you are registering\n\n[Step X out of X]"
wrong_time_text = "<b>WARNING</b>\nThe Time you submitted is not recognized. Please submit a time for the call again with the following format:\n<code>hours:minutes | 15:00</code>\nAlso note that the time you input will be treated as GMT"
wrong_date_text = "<b>WARNING</b>\nThe Date you submitted is not recognized. Please submit a date for the call again with the following format:\n<code>day/month/year | 15/03/2019</code>"
past_date_text = "Please insert a date in the future. you cannot schedule calls for a past date."
past_time_text = "Please insert a time in the future. You cannot schedule calls for a past time."
text_input_argument = "<b>SCHEDULE A NEW CALL - ADD A {}</b>\nFollow this wizard to schedule a new call!\n\nPlease reply to this message with the <b>{}</b> for the call you are registering"
cancel_add_call_text = "<b>CALL SCHEDULING CANCELLED</b>\nThe call hasn't been scheduled"

# FEEDBACK CONVERSATION MESSAGES TEXT
select_feedback_type = "Select below the type of <b>feedback</b> you are giving:"
send_feedback_input = "Reply to this message with the feedback you want to send:"
select_issue_type = "Select below the command you are having an <b>issue</b> with. If you are trying to report another issue, select 'Other'"
send_issue_input = "Reply to this message describing the issye you have encountered in order to send your feedback:"
cancel_feedback_text = "<b>FEEDBACK INPUT CANCELLED</b>\nNo feedback has been sent"

# EDIT GROUP CONVERSATION TEXT
no_permission_edit_group = '<b>This group has not been activated yet</b> Before editing this group\'s info, please activate it using /activate'
edit_category_text = 'Select below the new <b>category</b> for this group:'
edit_restriction_text = 'Select below the new <b>restriction</b> for this group:'
edit_region_text = 'Select below the correct <b>region</b> this group concerns:'
edit_color_text = 'Select below a new <b>color</b> for this group:'
edit_purpose_text = 'Reply to this message with the updated <b>purpose</b> of this group:'
edit_onboarding_text = 'Reply to this message with the updated <b>onboarding</b> procedure for this group:'
edit_is_subgroup_text = 'Select below weather this group is a sub-group of another group or not'
edit_parent_text = 'Select below the new <b>parent group</b> for this group'
no_parents_edit_parent = 'Cannot add a parent group to this group as no other group has been activated yet.'
editing_group_text = 'Editing group\'s information... This might take a while'
edited_group_text = 'This group\'s information has been updated:'
cancel_edit_group_text = '<b>GROUP EDIT CANCELLED</b>\nThe group hasn\'t been edited'


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
    elif (database.get(chat_id)[0] == None):
        # GET ALL USERS
        users = chat.get_administrators()
        # SAVE GROUP INSTANCE IN PICKLE
        group = Group(
            id=chat_id,
            title=title,
            users=users,
            platform="Telegram",
            activator_id=user_id,
            activator_name=update.effective_user.name,
            user_id=user_id,
            message=update.message
        )

        # CREATE MARKUP FOR CATEOGORY CHOICE:
        markup = create_menu(
            [interface.trelloc.WORKING_GROUP, interface.trelloc.DISCUSSION_GROUP, interface.trelloc.PROJECT], [interface.trelloc.WORKING_GROUP, interface.trelloc.DISCUSSION_GROUP, interface.trelloc.PROJECT])

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
    if user_id != group.activator_id:
        return CATEGORY
    else:
        group.category = query.data

    # SET NEW TEXT AND MARKAP FOR LEVEL REQUEST
    text = "Ok, cool!\nNow please select the <b>region</b> this group concerns: "
    markup = create_menu(["Africa", "Asia", "North America", "South America", "Oceania", "Europe", "Global"], [
        interface.trelloc.regions['Africa'],
        interface.trelloc.regions['Asia'],
        interface.trelloc.regions['North America'],
        interface.trelloc.regions['South America'],
        interface.trelloc.regions['Oceania'],
        interface.trelloc.regions['Europe'],
        interface.trelloc.regions['Global']], 2)
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
    if user_id != group.activator_id:
        return REGION
    else:
        group.region = utils.getKeysByValue(
            interface.trelloc.regions, query.data)[0]

    # SET NEW TEXT AND MARKAP FOR RESTRICTION REQUEST
    text = "Cool! Next, please select the <b>access level</b> for this this group: \n\n<b>Open</b> - Any fff activist working on the international level is allowed to enter\n\n<b>Restricted</b> - Some level of restriction (example: n. activists per country/region\n\n<b>Closed</b> - The group is closed"

    markup = create_menu(["Open", "Restricted", "Closed"],
                         [interface.trelloc.restrictions['Open'],
                          interface.trelloc.restrictions['Restricted'],
                          interface.trelloc.restrictions['Closed']])
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
    if user_id != group.activator_id:
        return RESTRICTION
    else:
        group.restriction = utils.getKeysByValue(
            interface.trelloc.restrictions, query.data)[0]

    # SET NEW TEXT AND MARKAP FOR IS SUBGOUP REQUEST
    text = "Awesome. Is this chat a sub-group of any working/discussion group in fridays for future? Answer by clicking the buttons below:"
    markup = create_menu(["No", "Yes"], [0, 1], cols=2)
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
    if user_id != group.activator_id:
        return IS_SUBGROUP

    print("BOT - IS SUBGROUP: Query:", query.data, " type: ", type(query.data))
    if query.data == str(1):
        print("BOT: Select parents")
        group.is_subgroup = True

        # SET NEW TEXT AND MARKAP FOR PARENT REQUEST
        if database.get()[0] != None:
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
            group.is_subgroup = False
            markup = create_menu(["Next"], [0])
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
        markup = create_menu(["Skip"], ["skip"])
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
    if user_id != group.activator_id:
        return PARENT_GROUP

    if query.data == 'no_parent':
        group.is_subgroup = False
        # SET NEW TEXT AND MARKAP FOR PURPOSE REQUEST
        text = "Alright, last two steps! Please reply to this message with a short description of the purpose and mandate of the group.\nYou can skip this step by clicking the button below."
        markup = create_menu(["Skip"], ["skip"])
        query.edit_message_text(text, parse_mode=ParseMode.HTML)
        query.edit_message_reply_markup(markup)
        group.message = query.message
        utils.dump_pkl('newgroup', group)
        return PURPOSE
    elif query.data in (0, 1):
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
        markup = create_menu(["Skip"], ["skip"])
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
    if user_id != group.activator_id:
        return PURPOSE

    try:
        query = update.callback_query
        query.answer()
        text = "Alright, we'll skip that. Last question:\nPlease reply to this message with a description of who is allowed access to this group and how can activists join this group. You can skip this step as well with the button below."
        markup = create_menu(["Skip"], ["skip"])
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
        markup = create_menu(["Skip"], ["skip"])
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
    print('TELEBOT: onboarding(): Is Subgroup: ',
          group.is_subgroup, ' ', type(group.is_subgroup))
    if user_id != group.activator_id:
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


def save_group_info(chat, group):
    # GROUP SAVING: Chat id, Title, Admins, Category, Region, Restrictions, is_subgroup,  parentgroup, purpose, onboarding
    print("SAVE GROUP INFO -----------------------------")
    group.date = datetime.utcnow()
    card_url = interface.save_group(group)
    if card_url == -1:
        chat.send_message(
            text="There was a problem in adding the call to the database.\nPlease contact @davidwickerhf for technical support.")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton("Trello Card", url=str(
        card_url)), InlineKeyboardButton("Edit Info", callback_data='edit_group')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    print("BOT - Save Group Info: Made Kayboard")

    info_text = format_group_info(group)
    utils.delete_pkl('newgroup', group.id, group.activator_id)
    chat.send_message(
        text=info_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
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
    elif database.get(item_id=chat_id)[0] == None:
        print("BOT - Delete Group: Group is not registerred")
        update.message.reply_text(
            text="This group isn't registerred yet, thus it can't be deleted. Please register this group with the following command:\n/newgroup - This command will take you through a wizard to register this group's information into the FFF Transparency Database.")
        return ConversationHandler.END
    elif member.status == "creator":
        print("BOT - Delete Group: Command was sent by owner/admin")
        markup = create_menu(['NO!', 'Yes, delete the group'], [0, 1])
        group = database.get(chat_id)[0]
        group.message = update.message.reply_text(
            text="<b>WARNING</b>\nBy deleting a group, it's information will be erased from the database and from the Trello Board. All tied calls events will be deleted from both the Trello Board and Google Calendar. Be aware that this action cannot be undone. Use /archivegroup if you are simply archiving the group.\n\nAre you sure you want to delete this group permanently?", reply_markup=markup, parse_mode=ParseMode.HTML)

        # ADD GROUP TO PERSISTANCE
        group.user_id = user.id
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
        print('TELEBOT: delete_group(): User does not have permission. Group: ', group)
        print('Query user: ', user_id)
        query.answer()
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
            markup = create_menu(['No, don\'t', 'Yes, delete it'], [0, 1])
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
            interface.delete_group(group)
            text = "@{} Cool, this group's information has been deleted from the database, as well as the Trello Board. All call events have been erased.".format(
                query.from_user.username)
            query.edit_message_text(text=text)
            # DELETE PERSISTENCE FILE
            utils.delete_pkl('deletegroup', chat_id, user_id)
            return ConversationHandler.END


####################### EDIT GROUP FUNCTIONS #################################
@run_async
def edit_group(update, context):
    print('TELEBOT: edit_group()')
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    group = database.get(chat_id)[0]

    if group == None:
        update.effective_chat.send_message(
            no_permission_edit_group, parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    group.user_id = user_id
    group.children = database.get(group.id, field='parent_group')

    # Send Argument Menu
    markup = create_menu([
        'Category',
        'Restriction',
        'Region',
        'Color',
        'Purpose',
        'Onboarding',
        'Parent Group',
        'Cancel'
    ], [
        CATEGORY,
        RESTRICTION,
        REGION,
        COLOR,
        PURPOSE,
        ONBOARDING,
        PARENT_GROUP,
        'cancel_edit_group'
    ], 2)

    if update.callback_query:
        update.callback_query.edit_message_text(
            'Select below what you wish to edit:', reply_markup=markup)
        group.message = update.callback_query.message
    else:
        group.message = update.message.reply_text(
            'Select below what you wish to edit:', reply_markup=markup)

    utils.dump_pkl('edit_group', group)
    return ARGUMENT


@run_async
def edit_group_argument(update, context):
    print('TELEBOT: edit_group_argument()')
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    query = update.callback_query

    # CANCEL is pressed
    if query.data == 'cancel_edit_group':
        cancel_edit_group(update, context)
        return ConversationHandler.END

    # RETRIEVE GROUP INFO
    group = utils.load_pkl('edit_group', chat_id, user_id)
    if group == '' or user_id != group.user_id:
        return ARGUMENT
    group.edit_argument = int(query.data)

    # HANDLE INPUT MARKUP
    markup = None
    if group.edit_argument == CATEGORY:
        print('TELEBOT: edit_group_argument(): Create Category Markup')
        markup = create_menu(
            [interface.trelloc.WORKING_GROUP, interface.trelloc.DISCUSSION_GROUP, interface.trelloc.PROJECT, 'Cancel'], [
                interface.trelloc.WORKING_GROUP, interface.trelloc.DISCUSSION_GROUP, interface.trelloc.PROJECT, 'cancel_edit_group'])
        text = edit_category_text
    elif group.edit_argument == RESTRICTION:
        print('TELEBOT: edit_group_argument(): Create Restriction Markup')
        markup = create_menu(["Open", "Restricted", "Closed", 'Cancel'],
                             [interface.trelloc.restrictions['Open'],
                              interface.trelloc.restrictions['Restricted'],
                              interface.trelloc.restrictions['Closed']])
        text = edit_restriction_text
    elif group.edit_argument == REGION:
        print('TELEBOT: edit_group_argument(): Create Region Markup')
        markup = create_menu(["Africa", "Asia", "North America", "South America", "Oceania", "Europe", "Global", 'Cancel'], [
            interface.trelloc.regions['Africa'],
            interface.trelloc.regions['Asia'],
            interface.trelloc.regions['North America'],
            interface.trelloc.regions['South America'],
            interface.trelloc.regions['Oceania'],
            interface.trelloc.regions['Europe'],
            interface.trelloc.regions['Global'],
            'cancel_edit_group'], 2)
        text = edit_region_text
    elif group.edit_argument == COLOR:
        print('TELEBOT: edit_group_argument(): Create Color Markup')
        markup = create_menu([
            interface.gcalendar.colors.get(1),
            interface.gcalendar.colors.get(2),
            interface.gcalendar.colors.get(3),
            interface.gcalendar.colors.get(4),
            interface.gcalendar.colors.get(5),
            interface.gcalendar.colors.get(6),
            interface.gcalendar.colors.get(7),
            interface.gcalendar.colors.get(8),
            interface.gcalendar.colors.get(9),
            interface.gcalendar.colors.get(10),
            'Cancel'
        ], [
            interface.gcalendar.LAVENDER,
            interface.gcalendar.SAGE,
            interface.gcalendar.GRAPE,
            interface.gcalendar.FLAMINGO,
            interface.gcalendar.BANANA,
            interface.gcalendar.TANGERINE,
            interface.gcalendar.PEACOCK,
            interface.gcalendar.GRAPHITE,
            interface.gcalendar.BLUEBERRY,
            interface.gcalendar.BASIL,
            'cancel_edit_group'

        ], cols=2)
        text = edit_color_text
    elif group.edit_argument == PURPOSE:
        print('TELEBOT: edit_group_argument(): Create Purpose Markup')
        markup = create_menu(['Cancel'], ['cancel_edit_group'])
        text = edit_purpose_text
    elif group.edit_argument == ONBOARDING:
        print('TELEBOT: edit_group_argument(): Create Onboarding Markup')
        text = edit_onboarding_text
        markup = create_menu(['Cancel'], ['cancel_edit_group'])
    elif group.edit_argument == PARENT_GROUP:
        print('TELEBOT: edit_group_argument(): Create Parent Markup')
        markup = create_menu(['Yes', 'No', 'Cancel'], [
                             0, 1, 'cancel_edit_group'], cols=2)
        query.edit_message_text(edit_is_subgroup_text,
                                parse_mode=ParseMode.HTML, reply_markup=markup)
        group.message = query.message
        utils.dump_pkl('edit_group', group)
        return EDIT_IS_SUBGROUP

    query.edit_message_text(text, parse_mode=ParseMode.HTML)
    try:
        query.edit_message_reply_markup(markup)
    except:
        print('TELEBOT: No Markup')
    group.message = query.message
    utils.dump_pkl('edit_group', group)
    return INPUT_ARGUMENT


@run_async
def edit_is_subgroup(update, context):
    print('TELEBOT: edit_is_subgroup()')
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    group = utils.load_pkl('edit_group', chat_id, user_id)

    if group == '' or group.user_id != user_id:
        return EDIT_IS_SUBGROUP

    query = update.callback_query
    if query.data == 'cancel_edit_group':
        cancel_edit_group(update, context)
        return ConversationHandler.END
    elif int(query.data) == 0:
        groups = database.get()
        print(
            'TELEBOT: edit_is_subgroup(): Group has parent | Database list: ', len(groups))
        if len(groups) <= 1:
            # No Parents available, error message, cancel edit operation
            query.edit_message_text(no_parents_edit_parent)
            utils.delete_pkl('edit_group', chat_id, user_id)
            return ConversationHandler.END

        group.is_subgroup = True
        markup = subgroup_menu(group, 1, method='edit_group')
        query.edit_message_text(edit_parent_text)
        query.edit_message_reply_markup(markup)
        group.message = query.message
        utils.dump_pkl('edit_group', group)
        return EDIT_PARENT
    elif int(query.data) == 1:
        print('TELEBOT: edit_is_subgroup(): Group does not have parent')
        group.message.edit_text(editing_group_text)
        group.is_subgroup = False
        group.parentgroup = ''
        # Save group into database and delete persistence file
        group = interface.edit_group(group)
        utils.delete_pkl('edit_group', chat_id, user_id)

        # Send confirmation message
        # Markup
        markup = InlineKeyboardMarkup([[InlineKeyboardButton(
            'Trello Card', url=group.card_url), InlineKeyboardButton('Edit Info', callback_data='edit_group')]])
        group.message.delete()
        text = format_group_info(group, type=1)
        update.effective_chat.send_message(
            text, reply_markup=markup, parse_mode=ParseMode.HTML)
        # End Conversation
        return ConversationHandler.END


@run_async
def edit_parent(update, context):
    print('TELEBOT: edit_parent()')
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    group = utils.load_pkl('edit_group', chat_id, user_id)

    if group == '' or group.user_id != user_id:
        return EDIT_PARENT

    query = update.callback_query
    if query.data == 'cancel':
        # Cancel Edit Group
        cancel_edit_group(update, context)
        return ConversationHandler.END
    elif query.data in (0, 1):
        markup = subgroup_menu(
            group=group, direction=query.data, method='edit_group')
        query.edit_message_reply_markup(markup)
        group.message = query.message
        utils.dump_pkl('edit_group', group)
        return EDIT_PARENT

    group.message.edit_text(editing_group_text)
    group.parentgroup = query.data
    # Save group into database and delete persistence file
    group = interface.edit_group(group)
    utils.delete_pkl('edit_group', chat_id, user_id)

    # Send confirmation message
    # Markup
    markup = InlineKeyboardMarkup([[InlineKeyboardButton(
        'Trello Card', url=group.card_url), InlineKeyboardButton('Edit Info', callback_data='edit_group')]])
    group.message.delete()
    text = format_group_info(group, type=1)
    update.effective_chat.send_message(
        text, reply_markup=markup, parse_mode=ParseMode.HTML)
    # End Conversation
    return ConversationHandler.END


@run_async
@send_typing_action
def input_edit_group_argument(update, context):
    print('TELEBOT: input_edit_group_argument()')
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    group = utils.load_pkl('edit_group', chat_id, user_id)

    if group == '' or group.user_id != user_id:
        return INPUT_ARGUMENT

    query = update.callback_query
    try:
        if query.data == 'cancel_edit_group':
            cancel_edit_group(update, context)
    except:
        print('TELEBOT: Not Cancel')
    group.message.edit_text(editing_group_text)

    if group.edit_argument == CATEGORY:
        print('TELEBOT: input_edit_group_argument(): Category')
        group.category = query.data
    elif group.edit_argument == RESTRICTION:
        print('TELEBOT: input_edit_group_argument(): Restriction')
        group.restriction = utils.getKeysByValue(
            interface.trelloc.restrictions, query.data)[0]
    elif group.edit_argument == REGION:
        print('TELEBOT: input_edit_group_argument(): Region')
        group.region = utils.getKeysByValue(
            interface.trelloc.regions, query.data)[0]
    elif group.edit_argument == COLOR:
        print('TELEBOT: input_edit_group_argument(): Color')
        group.color = query.data
    elif group.edit_argument == PURPOSE:
        print('TELEBOT: input_edit_group_argument(): Purpose')
        group.purpose = update.message.text
    elif group.edit_argument == ONBOARDING:
        print('TELEBOT: input_edit_group_argument(): Onboarding')
        group.onboarding = update.message.text
    elif group.edit_argument == PARENT_GROUP:
        print('TELEBOT: input_edit_group_argument(): Parent group')
        group.parentgroup = query.data

    # Save group into database and delete persistence file
    group = interface.edit_group(group)
    utils.delete_pkl('edit_group', chat_id, user_id)

    # Send confirmation message
    # Markup
    text = format_group_info(group, type=1)
    print('TELEBOT: group card url: ', group.card_url)
    keyboard = [[InlineKeyboardButton("Trello Card", url=str(
        group.card_url)), InlineKeyboardButton("Edit Info", callback_data='edit_group')]]
    markup = InlineKeyboardMarkup(keyboard)
    group.message.delete()
    update.effective_chat.send_message(
        text, reply_markup=markup, parse_mode=ParseMode.HTML)
    # End Conversation
    return ConversationHandler.END

@run_async
@send_typing_action
def cancel_edit_group(update, context):
    # GET CALL SAVED IN PERSISTANCE FILE
    chat_id = update.effective_chat.id
    user_id = update.callback_query.from_user.id
    group = utils.load_pkl('edit_group', chat_id, user_id)
    update.callback_query.answer()
    if group == "" or user_id != group.user_id:
        return
    else:
        print("CANCEL PRESSED")
        group.message.edit_text(
            text=cancel_edit_group_text, parse_mode=ParseMode.HTML)
        utils.delete_pkl('edit_group', chat_id, user_id)
    return ConversationHandler.END


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


def format_group_info(group, type=0):
    print('TELEBOT: format_group_info()')
    if type == 0:
        text = '<b>{}</b> has been saved in the database!'.format(group.title)
    elif type == 1:
        text = edited_group_text
    text = text +  '''\n<b>Category:</b> {}\n<b>Restriction:</b> {}\n<b>Region:</b> {}\n<b>Color:</b> {}\n<b>Purpose:</b> {}\n<b>Onboarding:</b> {}'''.format(
        group.category, group.restriction, group.region, group.get_color(), group.purpose, group.onboarding)
    if group.is_subgroup:
        text = text + \
            '\n<b>Parent Group:</b> {}'.format(
                database.get_group_title(group.parentgroup))
    return text

    
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
    name = user.name

    print("Got chat id")

    if groupchat.id == user.id:
        # CHAT IS USER
        print("Chat is user")
        groupchat.send_message(
            text=new_call_onlygroups_message)
        return ConversationHandler.END
    elif database.get(item_id=update.message.chat.id)[0] == None:
        # CHAT IS NOT REGISTERED
        print("Chat is not registered yet")
        text = chat_not_registerred.format(
            new_group_description)
        groupchat.send_message(
            text=text, parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    else:
        # EVERYTHING OK
        message_text = update.message.text + ' '
        print("Message Text: " + message_text)
        command = message_text[:message_text.find(' ') + 1]
        print(command)
        # ALGORITHM IS NOT WORKING - AND IS SLOW
        propcall = Call(chat_id=chat_id, user_id=user_id,
                        message_id=message_id, name=name, message=message)
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
        # USER DID NOT START CONVERSATION
        return ADD_DATE

    print("ADD CALL DATE")
    print("Requesting user input")
    date_text = update.message.text
    print("Date Text: " + date_text)
    if utils.str2date(date_text) != -1:
        # INPUT IS CORRECT
        date = utils.str2date(date_text)

        # CHECK PAST DATE
        now = datetime.now(tz=pytz.utc).date()
        if date >= now:
            # DATE IS IN THE FUTURE
            call.date = date
            print("Date is valid: ", call.date)
        else:
            # DATE IS IN THE PAST
            keyboard = [[InlineKeyboardButton(
                "Cancel", callback_data="cancel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            call.message.delete()
            call.message = update.message.reply_text(
                text=past_date_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            utils.dump_pkl('newcall', call)
            return ADD_DATE
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
        local_tz = get_localzone()
        time = utils.str2time(message_text)
        offset = timedelta(minutes=45)
        now = datetime.now(tz=local_tz).astimezone(pytz.utc) - offset

        if call.date == now.date():
            if time >= now.time():
                # TIME IS ACCEPTABLE
                call.time = time
            else:
                # TIME IS IN THE PAST
                keyboard = [[InlineKeyboardButton(
                    "Cancel", callback_data="cancel")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                call.message.delete()
                call.message = update.message.reply_text(
                    text=past_time_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
                utils.dump_pkl('newcall', call)
                return ADD_TIME
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
    message = update.message.chat.send_message(
        text="Saving call information... This might take a minute...")
    call.name = update.effective_chat.get_member(call.user_id).user.name
    values = interface.save_call(call)
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


######################### FEEDBACK CONVERSATION FUNCTIONS ###############
@run_async
def feedback(update, context):
    print("TELEBOT: feedback()")
    # Create Feedback Type Menu & Message Text
    markup = create_menu([
        interface.githubc.label_keys.get(interface.githubc.ISSUE),
        interface.githubc.label_keys.get(interface.githubc.FEATURE_REQUEST),
        interface.githubc.label_keys.get(interface.githubc.FEEDBACK),
        interface.githubc.label_keys.get(interface.githubc.QUESTION),
        'Cancel'
    ], [
        interface.githubc.ISSUE,
        interface.githubc.FEATURE_REQUEST,
        interface.githubc.FEEDBACK,
        interface.githubc.QUESTION,
        'cancel_feedback'
    ])

    # Create Feedback Obj
    feedback = Feedback(
        user_id=update.effective_user.id,
        chat_id=update.effective_chat.id,
        date=utils.now_time()
    )

    # Send Message
    feedback.message = update.message.chat.send_message(
        text=select_feedback_type, parse_mode=ParseMode.HTML, reply_markup=markup)

    # Save feedback obj in pickle
    utils.dump_pkl('feedback', feedback)
    return FEEDBACK_TYPE


@run_async
def feedback_type(update, context):
    print('TELEBOT: feedback_type()')
    # Retrieve Feedback Obj from pickle
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    feedback = utils.load_pkl('feedback', chat_id, user_id)

    if feedback == '' or user_id != feedback.user_id:
        print('TELEBOT: feedback_type: Wrong User')
        return FEEDBACK_TYPE

    # Check if callback-query is 'cancel_feedback'
    if update.callback_query.data == 'cancel_feedback':
        cancel_feedback(update, context)
        return ConversationHandler.END

    # Save selected type in obj
    feedback.type = int(update.callback_query.data)
    print('TELEBOT: feedback_type(): Got Feedback Type: ', feedback.type)
    if feedback.type == interface.githubc.ISSUE:
        # TYPE IS ISSUE
        # Send issue type menu
        markup = create_menu(button_titles=[
            interface.githubc.issue_types.get(interface.githubc.ACTIVATE),
            interface.githubc.issue_types.get(interface.githubc.ALL_GROUPS),
            interface.githubc.issue_types.get(interface.githubc.ARCHIVE_GROUP),
            interface.githubc.issue_types.get(
                interface.githubc.UNARCHIVE_GROUP),
            interface.githubc.issue_types.get(interface.githubc.DELETE_GROUP),
            interface.githubc.issue_types.get(interface.githubc.NEW_CALL),
            interface.githubc.issue_types.get(interface.githubc.ALL_CALLS),
            interface.githubc.issue_types.get(interface.githubc.DELETE_CALL),
            interface.githubc.issue_types.get(interface.githubc.TRUST_USER),
            interface.githubc.issue_types.get(interface.githubc.OTHER),
            'Cancel'
        ], callbacks=[
            interface.githubc.ACTIVATE,
            interface.githubc.ALL_GROUPS,
            interface.githubc.ARCHIVE_GROUP,
            interface.githubc.UNARCHIVE_GROUP,
            interface.githubc.DELETE_GROUP,
            interface.githubc.NEW_CALL,
            interface.githubc.ALL_CALLS,
            interface.githubc.DELETE_CALL,
            interface.githubc.TRUST_USER,
            interface.githubc.OTHER,
            'cancel_feedback'
        ], cols=2)
        print('TELEBOT: issue_type(): Created Markup')
        update.callback_query.edit_message_text(
            select_issue_type, parse_mode=ParseMode.HTML)
        update.callback_query.edit_message_reply_markup(markup)
        feedback.message = update.callback_query.message
        # Save feedback obj in pickle
        utils.dump_pkl('feedback', feedback)
        return ISSUE_TYPE
    else:
        # TYPE IS EITHER QUESTION, FEEDBACK OR FEATURE REQUEST
        # Send message asking for input
        print('TELEBOT: Feedback is NOT an issue')
        markup = create_menu('Canel', 'cancel_feedback')
        update.callback_query.edit_message_text(send_feedback_input.format(
            interface.githubc.label_keys.get(feedback.type)), parse_mode=ParseMode.HTML)
        feedback.message = update.callback_query.message
        # Save feedback obj in pickle
        utils.dump_pkl('feedback', feedback)
        return INPUT_FEEDBACK


@run_async
def issue_type(update, context):
    print('TELEBOT: issue_feedback()')
    # Retrieve feedback obj from pickle
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    feedback = utils.load_pkl('feedback', chat_id, user_id)
    print('TELEBOT: issue_type')

    if feedback == '' or user_id != feedback.user_id:
        return ISSUE_TYPE

    # Check if callback-query is 'cancel_feedback'
    if update.callback_query.data == 'cancel_feedback':
        cancel_feedback(update, context)
        return ConversationHandler.END

    # Save selected status (issue type) in obj
    feedback.issue_type = int(update.callback_query.data)

    # Send message requesting issue description
    markup = create_menu('Canel', 'cancel_feedback')
    update.callback_query.edit_message_text(send_issue_input.format(
        interface.githubc.label_keys.get(feedback.type)), parse_mode=ParseMode.HTML)
    feedback.message = update.callback_query.message
    # Save feedback obj in pickle
    utils.dump_pkl('feedback', feedback)
    return INPUT_FEEDBACK


@run_async
@send_typing_action
def input_feedback(update, context):
    print('TELEBOT: issue_type()')
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    feedback = utils.load_pkl('feedback', chat_id, user_id)

    if feedback == '' or user_id != feedback.user_id:
        return INPUT_FEEDBACK

    # Processing Message
    feedback.message.delete()
    feedback.message = update.message.reply_text('Processing...')

    # Save issue
    message_text = save_feedback(feedback, update)

    # Send message to developer
    devs = settings.get_var('DEVS')
    for dev_id in devs:
        context.bot.send_message(dev_id, message_text,
                                 parse_mode=ParseMode.HTML)

    # Send confirm message in chat
    feedback.message.delete()
    text = '{} thank you for your feedback! Your input has been sent to my developers'.format(
        update.effective_user.name)
    update.effective_chat.send_message(text, parse_mode=ParseMode.HTML)

    # Delete Persistence File
    utils.delete_pkl('feedback', chat_id, user_id)
    return ConversationHandler.END


def save_feedback(feedback, update):
    # Format feedback body
    type_int = feedback.get_type()
    issue_type_int = feedback.get_issue_type()
    body = '''**{} by {}:**
    **Issue Type:** {}
    **Recorded on:** {}
    **User id:** {}
    **Chat id:** {}
    **Chat Name:** {}
    **Issue Body:** {}'''.format(
        interface.githubc.label_keys.get(type_int),
        update.effective_user.name,
        interface.githubc.issue_types.get(issue_type_int),
        feedback.date,
        feedback.user_id,
        feedback.chat_id,
        update.effective_chat.title,
        update.message.text)
    feedback.body = body
    feedback.title = '{} by {}'.format(
        interface.githubc.label_keys.get(feedback.type), update.effective_user.name,)

    # Save feedback in database / GitHub
    feedback = interface.feedback(feedback)

    # Send message to developers
    message = '<b>{} by {}</b>:\n\n<b>Issue Type:</b> {}\n<b>Recorded on:</b> {}\n<b>User id:</b> {}\n<b>Chat id:</b> {}\n<b>Chat Name:</b> {}\n<b>Issue Body:</b> {}\n<b>Issue Url</b>: {}\n<b>Issue Json:</b> {}'.format(
        interface.githubc.label_keys.get(feedback.type),
        mention_html(update.effective_user.id,
                     update.effective_user.first_name),
        interface.githubc.issue_types.get(feedback.issue_type),
        feedback.date,
        feedback.user_id,
        feedback.chat_id,
        update.effective_chat.title,
        update.message.text,
        feedback.url,
        feedback.json)
    return message


@run_async
@send_typing_action
def cancel_feedback(update, context):
    # GET CALL SAVED IN PERSISTANCE FILE
    chat_id = update.effective_chat.id
    user_id = update.callback_query.from_user.id
    feedback = utils.load_pkl('feedback', chat_id, user_id)
    update.callback_query.answer()
    if feedback == "" or user_id != feedback.user_id:
        return
    else:
        print("CANCEL PRESSED")
        feedback.message.edit_text(
            text=cancel_feedback_text, parse_mode=ParseMode.HTML)
        utils.delete_pkl('feedback', chat_id, user_id)
    return ConversationHandler.END


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
        entry_points=[CommandHandler("activate", save_group)],
        states={
            GROUP_INFO: [],
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
    edit_group_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(
            edit_group, pattern='^' + 'edit_group' + '$'), CommandHandler('editgroup', edit_group)],
        states={
            ARGUMENT: [CallbackQueryHandler(edit_group_argument)],
            EDIT_IS_SUBGROUP: [CallbackQueryHandler(edit_is_subgroup)],
            EDIT_PARENT: [CallbackQueryHandler(edit_parent)],
            INPUT_ARGUMENT: [CallbackQueryHandler(input_edit_group_argument), MessageHandler(Filters.text, input_edit_group_argument)],
        },
        fallbacks=[CallbackQueryHandler(
            cancel_feedback, pattern='cancel_feedback')]
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
    feedback_handler = ConversationHandler(
        entry_points=[CommandHandler('feedback', feedback)],
        states={
            FEEDBACK_TYPE: [CallbackQueryHandler(feedback_type)],
            ISSUE_TYPE: [CallbackQueryHandler(issue_type)],
            INPUT_FEEDBACK: [MessageHandler(Filters.text, input_feedback)]
        },
        fallbacks=[CallbackQueryHandler(
            cancel_feedback, pattern='cancel_feedback')],
    )

    dp.add_handler(group_handler)
    dp.add_handler(edit_group_handler)
    dp.add_handler(delete_group_handler)
    dp.add_handler(call_handler)
    dp.add_handler(feedback_handler)
    dp.add_error_handler(error)

    thread = Thread(target=dp.start, name='dispatcher')
    thread.start()

    return update_queue
