from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, ReplyKeyboardMarkup, ChatAction
from telegram.ext.dispatcher import run_async
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from functools import wraps
import json
import logging
import os
from modules import utils
from modules import database
from modules import settings

if os.environ.get('PORT') in (None, ""):
    # CODE IS RUN LOCALLY
    local = True
    print("BOT: Code running locally")
else:
    # CODE IS RUN ON SERVER
    settings.set_enviroment()
    local = False
    print("BOT: Code running on server")


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("telegram.bot")

# GLOBAL VARIABLES - CALL CONVERSATION
CALL_DETAILS, EDIT_CALL, EDIT_ARGUMENT, ADD_TITLE, ADD_DATE, ADD_TIME = range(
    6)
global_missing_arguments = []
saving = ["", "", "", "", "", ""]
add_call_message = ""
global_user_id = ""

# GLOBAL VARIABLES - GROUP CONVERSATION
GROUP_INFO, EDIT_GROUP, CATEGORY, REGION, RESTRICTION, IS_SUBGROUP, PARENT_GROUP, PURPOSE, MANDATE, ONBOARDING = range(
    10)
# GROUP SAVING: Chat id, Title, Admins, Category, Region, Restrictions, is_subgroup,  parentgroup, purpose, onboarding
group_saving = ["", "", "", "", "", "", "", "", "", ""]
add_group_message = ""
last_index = ""

# GLOBAL VARIABLES - DELETE GROUP CONVERSATION
CANCEL_DELETE_GROUP, CONFIRM_DELETE_GROUP, DOUBLE_CONFIRM_DELETE_GROUP = range(
    3)
delete_group_message = ""


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
text_input_argument = "<b>SCHEDULE A NEW CALL - ADD A {}</b>\nFollow this wizard to schedule a new call!\n\nPlease reply to this message with the <b>{}</b> for the call you are registering\n\n[Step {} out of {}]"
cancel_add_call_text = "<b>CALL SCHEDULING CANCELLED</b>\nThe call hasn't been scheduled"


def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context,  *args, **kwargs)

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


def save_group(update, context):
    print("BOT: --- SAVE GROUP INFO ---")
    # GET GROUP INFORMATION
    chat = update.message.chat
    title = chat.title
    chat_id = chat.id
    if chat_id == update.message.from_user.id:
        print("Chat is user")
        update.message.chat.send_message(
            text="This command can be run only in group chats")
        return ConversationHandler.END
    elif (database.find_row_by_id("groups", chat_id)[0] == -1):
        # SAVE INFO IN GLOBAL LIST
        global group_saving
        global add_group_message
        global global_user_id
        admins = chat.get_administrators()
        group_saving = [chat_id, title, admins, "", "",
                        "Telegram", "", "", "", "", "", "", "", ""]
        global_user_id = update.message.from_user.id

        # CREATE MARKUP FOR CATEOGORY CHOICE:
        markup = group_menu(
            [database.trelloc.WORKING_GROUP, database.trelloc.DISCUSSION_GROUP, database.trelloc.PROJECT], [database.trelloc.WORKING_GROUP, database.trelloc.DISCUSSION_GROUP, database.trelloc.PROJECT])

        # SEND MESSAGE WITH INTRO AND REQUEST OF CATEGORY
        add_group_message = chat.send_message(
            text=save_group_message, parse_mode=ParseMode.HTML, reply_markup=markup)
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


def category(update, context):
    print("BOT: --- CATEGORY ---")
    query = update.callback_query
    if update.callback_query.from_user.id != global_user_id:
        update.callback_query.answer()
        return
    global group_saving
    global add_group_message
    group_saving[3] = query.data
    add_group_message = query.message
    query.answer()

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
    print("BOT - CATEGORY: Created Markup")
    # EDIT MESSAGE TEXT AND MARKUP -  REQUEST REGION
    query.edit_message_text(text, parse_mode=ParseMode.HTML)
    query.edit_message_reply_markup(markup)
    return REGION


def region(update, context):
    print("BOT: --- LEVEL ---")
    query = update.callback_query
    if update.callback_query.from_user.id != global_user_id:
        update.callback_query.answer()
        return
    global group_saving
    global add_group_message
    region_title = utils.getKeysByValue(
        database.trelloc.regions, query.data)[0]
    group_saving[4] = region_title
    add_group_message = query.message
    query.answer()

    # SET NEW TEXT AND MARKAP FOR RESTRICTION REQUEST
    text = "Cool! Next, please select the <b>access level</b> for this this group: \n\n<b>Open</b> - Any fff activist working on the international level is allowed to enter\n\n<b>Restricted</b> - Some level of restriction (example: n. activists per country/region\n\n<b>Closed</b> - The group is closed"
    markup = group_menu(["Open", "Restricted", "Closed"],
                        [database.trelloc.restrictions['Open'],
                         database.trelloc.restrictions['Restricted'],
                         database.trelloc.restrictions['Closed']])
    query.edit_message_text(text, parse_mode=ParseMode.HTML)
    query.edit_message_reply_markup(markup)
    return RESTRICTION


def restriction(update, context):
    print("BOT: --- RESTRICTION ---")
    query = update.callback_query
    if update.callback_query.from_user.id != global_user_id:
        update.callback_query.answer()
        return
    global group_saving
    global add_group_message
    restriction_title = utils.getKeysByValue(
        database.trelloc.restrictions, query.data)[0]
    group_saving[5] = restriction_title
    add_group_message = query.message
    query.answer()

    # SET NEW TEXT AND MARKAP FOR IS SUBGOUP REQUEST
    text = "Awesome. Is this chat a sub-group of any working/discussion group in fridays for future? Answer by clicking the buttons below:"
    markup = group_menu(["No", "Yes"], [0, 1])
    query.edit_message_text(text, parse_mode=ParseMode.HTML)
    query.edit_message_reply_markup(markup)
    return IS_SUBGROUP


def is_subgroup(update, context):
    print("BOT: --- IS SUBGROUP ---")
    query = update.callback_query
    if update.callback_query.from_user.id != global_user_id:
        update.callback_query.answer()
        return
    global group_saving
    global add_group_message
    print("BOT - IS SUBGROUP: Query:", query.data, " type: ", type(query.data))
    if query.data == str(1):
        print("BOT: Select parents")
        group_saving[6] = "Yes"
        add_group_message = query.message
        query.answer()
        # SET NEW TEXT AND MARKAP FOR PARENT REQUEST
        if len(database.get_all_groups()) > 0:
            print("BOT: Groups found")
            text = "Alright, select below the parent group of this group chat:"
            global last_index
            last_index = 1
            markup = subgroup_menu(first_index=last_index, direction=1, size=5)
            query.edit_message_reply_markup(markup)
            return PARENT_GROUP
        else:
            print("BOT: No groups available for parents")
            text = "Mmh... It seams no other group has been registerred yet... To add a parent to a group, make sure you register that groupchat first!"
            markup = group_menu(["Next"], [0])
            query.edit_message_text(text, parse_mode=ParseMode.HTML)
            query.edit_message_reply_markup(markup)
            return IS_SUBGROUP
    elif query.data == str(0):
        print("BOT: No parents")
        group_saving[6] = "No"
        add_group_message = query.message
        query.answer()
        # SET NEW TEXT AND MARKAP FOR PURPOSE REQUEST
        text = "Alright, last two steps! Please reply to this message with a short description of the purpose and mandate of the group.\nYou can skip this step by clicking the button below."
        markup = group_menu(["Skip"], ["skip"])
        query.edit_message_text(text, parse_mode=ParseMode.HTML)
        query.edit_message_reply_markup(markup)
        return PURPOSE


def parent_group(update, context):
    print("BOT: --- PARENT GROUP ---")
    query = update.callback_query
    if update.callback_query.from_user.id != global_user_id:
        update.callback_query.answer()
        return
    global add_group_message
    if query.data == str(0) or str(1):
        global last_index
        markup = subgroup_menu(first_index=last_index, direction=query.data)
        query.edit_message_reply_markup(markup)
        add_group_message = query.message
        query.answer()
        return PARENT_GROUP
    else:
        global group_saving
        parent_id = query.data
        group_saving[7] = parent_id

        # SET NEW TEXT AND MARKAP FOR PURPOSE REQUEST
        text = "Great! Lasto two steps! Please reply to this message with a short description of the purpose and mandate of the group.\nYou can skip this step by clicking the button below."
        markup = group_menu(["Skip"], ["skip"])
        query.edit_message_text(text, parse_mode=ParseMode.HTML)
        query.edit_message_reply_markup(markup)
        add_group_message = query.message
        query.answer()
        return PURPOSE


def purpose(update, context):
    print("BOT: --- PURPOSE ---")
    global add_group_message
    try:
        if update.message.from_user.id != global_user_id:
            return
    except:
        if update.callback_query.from_user.id != global_user_id:
            update.callback_query.answer()
            return
    try:
        query = update.callback_query
        query.answer()
        text = "Alright, we'll skip that. Last question:\nPlease reply to this message with a description of who is allowed access to this group and how can activists join this group. You can skip this step as well with the button below."
        markup = group_menu(["Skip"], ["skip"])
        query.edit_message_text(text, parse_mode=ParseMode.HTML)
        query.edit_message_reply_markup(markup)
        return ONBOARDING
    except:
        print("BOT: USer sent messages")
        global group_saving
        group_saving[8] = update.message.text

        # SET NEW TEXT AND MARKAP FOR PURPOSE REQUEST
        text = "Great! Last step!\nPlease reply to this message with a description of who is allowed access to this group and how can activists join this group. You can skip this step as well with the button below."
        markup = group_menu(["Skip"], ["skip"])
        print("BOT: Set up text and markup")
        add_group_message.edit_text(
            text=text, parse_mode=ParseMode.HTML, reply_markup=markup)
        print("BOT: Edited")
        print("BOT: Change message to get Onboarding")
        return ONBOARDING


@send_typing_action
def onboarding(update, context):
    print("BOT: --- ONBOARDING ---")
    try:
        if update.message.from_user.id != global_user_id:
            return
    except:
        if update.callback_query.from_user.id != global_user_id:
            update.callback_query.answer()
            return
    query = update.callback_query
    global group_saving
    global add_group_message
    try:
        query.answer()
        add_group_message.delete()
        save_group_info(add_group_message.chat)
        print(group_saving)
        return ConversationHandler.END
    except:
        group_saving[9] = update.message.text
        save_group_info(update.message.chat)
        print(group_saving)
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


def subgroup_menu(first_index, direction, size=5):
    values = database.rotate_groups(
        first_index=first_index, direction=direction, size=size)
    rotated_groups = values[0]
    print("Check 1 ", rotated_groups)
    global last_index
    last_index = values[1]
    keyboard = []
    for group in rotated_groups:
        print("Check 2")
        row = []
        group_id = group[0]
        title = database.get_group_title(group_id)
        button = InlineKeyboardButton(text=title, callback_data=group_id)
        row.append(button)
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="<=", callback_data=0),
                     InlineKeyboardButton(text="=>", callback_data=1)])
    markup = InlineKeyboardMarkup(keyboard)
    return markup


def save_group_info(chat):
    # GROUP SAVING: Chat id, Title, Admins, Category, Region, Restrictions, is_subgroup,  parentgroup, purpose, onboarding
    print("BOT: --- SAVE GROUP INFO ---")
    card_url = database.save_group(chat_id=group_saving[0], title=group_saving[1], admins=group_saving[2],
                                   category=group_saving[3], region=group_saving[4], platform="Telegram", restriction=group_saving[5], date=datetime.now(), is_subgroup=group_saving[6], parentgroup=group_saving[7], purpose=group_saving[8], onboarding=group_saving[9])
    if card_url == -1:
        chat.send_message(
            text="There was a problem in adding the call to the database.\nPlease contact @davidwickerhf for technical support.")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton("Trello Card", url=str(
        card_url)), InlineKeyboardButton("Edit Info", callback_data="EDIT_GROUP")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    print("BOT - Save Group Info: Made Kayboard")

    text = "<b>{}</b> has been saved in the database!".format(group_saving[1])

    chat.send_message(
        text=text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    print("BOT - Save Group Info: Sent Reply")
####################### DELETE GROUP FUNCTIONS ##############################


def delete_group(update, context):
    print("BOT: --- DELETE GROUP ---")
    user = update.message.from_user
    group_id = update.message.chat.id
    global global_user_id
    global_user_id = user.id
    global delete_group_message
    member = update.message.chat.get_member(update.message.from_user.id)
    print("BOT: Member Status: ", member.status)
    if group_id == user.id:
        print("Chat is user")
        update.message.chat.send_message(
            text="This command can be run only in group chats")
        return ConversationHandler.END
    elif database.find_row_by_id(item_id=group_id)[0] == -1:
        print("BOT - Delete Group: Group is not registerred")
        delete_group_message = update.message.reply_text(
            text="This group isn't registerred yet, thus it can't be deleted. Please reigster this group with the following command:\n/newgroup - This command will take you through a wizard to register this group's information into the FFF Transparency Database.")
        return ConversationHandler.END
    if member.status == "creator":
        print("BOT - Delete Group: Command was sent by owner/admin")
        markup = group_menu(['NO!', 'Yes, delete the group'], [0, 1])
        delete_group_message = update.message.reply_text(
            text="<b>WARNING</b>\nBy deleting a group, it's information will be erased from the database and from the Trello Board. All tied calls events will be deleted from both the Trello Board and Google Calendar. Be aware that this action cannot be undone. Use /archivegroup if you are simply archiving the group.\n\nAre you sure you want to delete this group permanently?", reply_markup=markup, parse_mode=ParseMode.HTML)
        return CONFIRM_DELETE_GROUP
    else:
        owner_username = ""
        for admin in update.message.chat.get_administrators():
            if admin.status == "creator":
                owner_username = admin.user.username
        print("BOT - Delete Group: User does not have permission to delete the group")
        delete_group_message = update.message.reply_text(
            text="Sorry, you don't have permission to delete this group. Please ask the group owner to do it.\n@{}".format(owner_username))
        return ConversationHandler.END


def confirm_delete_group(update, context):
    print("BOT: --- CONFIRM DELETE GROUP ---")
    if update.callback_query.from_user.id != global_user_id:
        # USER DOES NOT HAVE PERMISSION TO DELETE BOT
        return CONFIRM_DELETE_GROUP
    else:
        query = update.callback_query
        query.answer()
        global delete_group_message
        print("BOT: Query Data: ", query.data, " Type: ", type(query.data))

        if query.data == str(0):
            # USER CLICKED DO NOT DELETE BUTTON
            text = "Alright, the group will not be deleted."
            query.edit_message_text(text, parse_mode=ParseMode.HTML)
            return ConversationHandler.END
        elif query.data == str(1):
            # USER CLICKED DELETE BUTTON
            markup = group_menu(['No, don\'t', 'Yes, delete it'], [0, 1])
            text = "Are you really, really sure you want to permanently delete this group's information?"
            query.edit_message_text(text=text, reply_markup=markup)
            return DOUBLE_CONFIRM_DELETE_GROUP
        print("BOT: Error in Query data in Confirm Delete Group")


@send_typing_action
def double_confirm_delete_group(update, context):
    print("BOT: --- DOUBLE CONFIRM DELETE GROUP ---")
    if update.callback_query.from_user.id != global_user_id:
        # USER DOES NOT HAVE PERMISSION TO DELETE BOT
        return CONFIRM_DELETE_GROUP
    else:
        query = update.callback_query
        query.answer()
        global delete_group_message
        if query.data == str(0):
            # USER CLICKED DO NOT DELETE BUTTON
            text = "Alright, the group will not be deleted."
            query.edit_message_text(text=text)
            return ConversationHandler.END
        elif query.data == str(1):
            # USER CLICKED DELETE BUTTON
            text = "Ok, this group is being being deleted... This might take a minute..."
            query.edit_message_text(text=text)
            database.delete_group(delete_group_message.chat.id, global_user_id)
            text = "@{} Cool, this group's information has been deleted from the database, as well as the Trello Board. All call events have been erased.".format(
                query.from_user.username)
            query.edit_message_text(text=text)
            return ConversationHandler.END
####################### CALL CONVERSATION FUNCTIONS #########################


@send_typing_action
def new_call(update, context):
    message = update.message
    message_id = message.message_id
    groupchat = update.message.chat
    global global_user_id
    user = message.from_user
    global_user_id = user.id
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
        command = message_text[:message_text.find(' ')+1]
        print(command)
        # ALGORITHM IS NOT WORKING - AND IS SLOW
        values = utils.format_string(message_text, command)

        arguments = values[0]
        missing_arguments = values[1]
        print(missing_arguments)

        # Reset Global Values
        global global_missing_arguments
        global saving
        if (len(global_missing_arguments) > 0):
            global_missing_arguments = global_missing_arguments.clear()
        saving = list(["", "", "", arguments[3], "", ""])

        # ARGUMENTS FORMAT: TITLE, DATE, TIME, DURATION, DESCRIPTION, AGENDA LINK
        if 0 in missing_arguments or 1 in missing_arguments or 2 in missing_arguments:

            global_missing_arguments = missing_arguments.copy()

            print("GET ARGUMENTS")
            if 0 in global_missing_arguments:
                print("Requesting Title input")
                # SEND MESSAGE
                format_input_argument(
                    update, 0, "Title", global_missing_arguments, global_missing_arguments.index(0))
                return ADD_TITLE
            elif 1 in global_missing_arguments:
                print("Title is not missing - Requesting Date input")
                # SEND MESSAGE
                format_input_argument(
                    update, 0, "Date", global_missing_arguments, global_missing_arguments.index(1))
                return ADD_DATE
            elif 2 in global_missing_arguments:
                print("Date is not missing - Requesting Time input")
                # SEND MESSAGE
                format_input_argument(
                    update, 0, "Time", global_missing_arguments, global_missing_arguments.index(2))
                return ADD_TIME

        print("Not returned get arguments -> ALL necessary arguments are alraedy given")
        # SAVE CALL TO DATABASE
        for argument in arguments[4:]:
            if argument == "":
                argument = "N/A"

        save_call_info(update=update, context=context, title=arguments[0], date=arguments[1], time=arguments[2],
                       duration=arguments[3], description=arguments[4], agenda_link=arguments[5])


def call_details(update, context):
    print("CALL DETAILS")


def edit_call(update, context):
    print("EDIT CALL")


def edit_argument(update, context):
    print("EDIT ARGUMENT")


@send_typing_action
def add_title(update, context):
    print("ADD CALL TITLE")
    print("Getting user input")
    if update.message.from_user.id != global_user_id:
        return ADD_TITLE
    title = update.message.text
    global saving
    saving[0] = title

    # Request Call Date Input
    if 1 in global_missing_arguments:
        format_input_argument(
            update, 1, "Date", global_missing_arguments, global_missing_arguments.index(1))
        return ADD_DATE
    elif 2 in global_missing_arguments:
        format_input_argument(
            update, 1, "Time", global_missing_arguments, global_missing_arguments.index(2))
        return ADD_TIME
    else:
        print("CONVERSATION END - send call details")
        # SAVE INFO IN DATABASE
        save_call_info(
            update=update, context=context, title=saving[0], date=str(saving[1]), time=str(saving[2]), duration=saving[3])
        return CALL_DETAILS


@send_typing_action
def add_date(update, context):
    if update.message.from_user.id != global_user_id:
        return ADD_DATE
    print("ADD CALL DATE")
    print("Requesting user input")
    date_text = update.message.text
    print("Date Text: " + date_text)
    if utils.str2date(date_text) != -1:
        # INPUT IS CORRECT
        date = utils.str2date(date_text)
        print("Date is valid: ", date)
        global saving
        saving[1] = date
        print("Date added to global list")
    else:
        # INPUT IS INCORRECT
        global add_call_message
        keyboard = [[InlineKeyboardButton("Cancel", callback_data="cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        add_call_message.delete()
        add_call_message = update.message.reply_text(
            text=wrong_date_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        return ADD_DATE

    if 2 in global_missing_arguments:
        format_input_argument(
            update, 1, "Time", global_missing_arguments, global_missing_arguments.index(2))
        print("Going to next step")
        return ADD_TIME
    else:
        print("CONVERSATION END - send call details")
        # SAVE INFO IN DATABASE
        save_call_info(
            update=update, context=context, title=saving[0], date=str(saving[1]), time=str(saving[2]), duration=saving[3])
        return CALL_DETAILS


@send_typing_action
def add_time(update, context):
    if update.message.from_user.id != global_user_id:
        return ADD_TIME
    print("ADD TIME")
    print("Requesting user input")
    message_text = update.message.text
    if utils.str2time(message_text) != -1:
        # INPUT IS CORRECT
        time = utils.str2time(message_text)
        print("Inputted time: ", str(time))
        global saving
        saving[2] = time
        print("CONVERSATION END - send call details")
        # SAVE INFO IN DATABASE
        save_call_info(
            update=update, context=context, title=saving[0], date=str(saving[1]), time=str(saving[2]), duration=saving[3])
        return ConversationHandler.END
    else:
        # INPUT IS INCORRECT
        global add_call_message
        keyboard = [[InlineKeyboardButton("Cancel", callback_data="cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        add_call_message.delete()
        add_call_message = add_call_message.reply_text(
            text=wrong_time_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


@send_typing_action
def cancel_call(update, context):
    try:
        if update.message.from_user.id != global_user_id:
            return
    except:
        if update.callback_query.from_user.id != global_user_id:
            print("BOT - CALL: Cancel Button Pressed with Query")
            update.callback_query.answer()
            return
    print("CANCEL PRESSED")
    global add_call_message
    add_call_message.edit_text(
        text=cancel_add_call_text, parse_mode=ParseMode.HTML)
    return ConversationHandler.END


def error(update, context):
    logger.warning('BOT: Update caused error: "%s"', context.error)


def format_input_argument(update, state, argument_title, missing, index):
    keyboard = [[InlineKeyboardButton(
        "Cancel", callback_data="cancel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    global add_call_message

    if state == 0:
        print("SEND FIRST GET ARGUMENTS MESSAGE")
        # Code runs for the first time -> Send message
        add_call_message = update.message.reply_text(text=text_input_argument.format(argument_title.upper(), argument_title, str(index+1), len(
            missing)), parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    else:
        # Code already run -> edit message
        add_call_message.delete()
        add_call_message = update.message.reply_text(text=text_input_argument.format(argument_title.upper(), argument_title, str(index+1), len(
            missing)), parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        print("EDIT GET ARGUMENTS MESSAGE")


@send_typing_action
def save_call_info(update, context, title, date, time, duration, description="", agenda_link=""):
    global add_call_message
    add_call_message.delete()
    username = update.message.from_user.username
    message = update.message.chat.send_message(
        text="Saving call information... This might take a minute...")

    values = database.save_call(
        message_id=update.message.message_id, chat_id=update.message.chat.id, title=title, date=date, time=time, user_id=update.message.from_user.id, duration=duration, description=description, agenda_link=agenda_link, username="@{}".format(username))
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

    text = utils.format_call_info(
        "save_call", title, date, time, duration, description, agenda_link)
    print("Formatted text")

    message.delete()
    update.message.reply_text(
        text=text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    print("Sent Reply")


def main():
    # - COMMENT WHEN DEPLOYING TO HEROKU
    TOKEN = settings.get_var('BOT_TOKEN')
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    if not local:
        # CODE IS RUN ON SERVER
        PORT = int(os.environ.get('PORT', '5000'))
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)
        updater.bot.set_webhook(
            "https://fff-transparency-wg.herokuapp.com/" + TOKEN)

    # Commands
    #dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_group))
    dp.add_handler(CommandHandler("help", help))
    #dp.add_handler(CommandHandler("newgroup", save_group))
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
        },
        fallbacks=[]
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
        },
        fallbacks=[CallbackQueryHandler(cancel_call)],
    )
    delete_group_handler = ConversationHandler(
        entry_points=[CommandHandler('deletegroup', delete_group)],
        states={
            CONFIRM_DELETE_GROUP: [CallbackQueryHandler(confirm_delete_group)],
            DOUBLE_CONFIRM_DELETE_GROUP: [
                CallbackQueryHandler(double_confirm_delete_group)]
        },
        fallbacks=[],
    )
    dp.add_handler(call_handler)
    dp.add_handler(group_handler)
    dp.add_handler(delete_group_handler)
    dp.add_error_handler(error)

    if local:
        updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
