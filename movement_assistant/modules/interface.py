from movement_assistant.modules.gcalendar import edit_event
import gspread
import os
import json
import pickle
from oauth2client.service_account import ServiceAccountCredentials
from movement_assistant.modules import gcalendar, trelloc, settings, utils, sheet, database, githubc
from movement_assistant.classes.group import Group
from movement_assistant.classes.call import Call
from movement_assistant.classes.user import User
from movement_assistant.classes.botupdate import BotUpdate
from datetime import datetime

REGULAR, ARCHIVED, DELETED = range(3)


def save_group(botupdate: BotUpdate):
    # REGISTER ALL USERS
    group = botupdate.obj
    users = []
    admins_string = ""
    for member in group.users:
        user = member.user
        first = 'N/A'
        last = 'N/A'
        username = 'N/A'
        if user.first_name != None:
            first = user.first_name
        if user.last_name != None:
            last = user.last_name
        if user.username != None:
            username = user.username
        obj = User(
            id=user.id,
            first=first,
            last=last,
            username=username,
            activator_id=group.activator_id
        )
        database.commit_user(obj)

        if member.status in ('creator', 'administrator'):
            user = member.user
            admins_string += "{}; ".format(user.name)

    admins_string = admins_string[:-2]
    group.admins_string = admins_string
    print("INTERFACE: Got Admins: ", group.admin_string)

    # GET RANDOM CALENDAR COLOR:
    color_id = utils.get_random_event_color()
    print("INTERFACE: Got Group Color")

    # CREATE TRELLO CARD
    if group.is_subgroup:
        parent_card = database.get_group_card(group.parentgroup)
        print("INTERFACE: Got parent card ", parent_card)
    else:
        parent_card = ""
        print("INTERFACE: No parent")
    card_info = trelloc.add_group(botupdate)
    card_id = card_info[0]
    card_url = card_info[1]
    print("INTERFACE: Got Trello Card Info")

    # SAVE GROUP IN DATABASE
    # Save Variables in Group Obj
    group.card_id = card_id
    group.color = color_id
    database.commit_group(group)
    print("INTERFACE: Saved group")

    # SHEET INTERFACE
    sheet.save_group(botupdate)
    return card_url


def edit_group(botupdate: BotUpdate):
    print('INTERFACE: edit_group()')
    # EDIT TRELLO CARD
    group = botupdate.obj
    group.children = database.get(group.id, field='parent_group')
    botupdate.old_obj = database.get(group.id)[0]
    botupdate.old_obj.siblings = database.get_siblings(botupdate.old_obj)
    group.siblings = database.get_siblings(group)
    
    trelloc.edit_group(botupdate)

    for event in database.get(table=database.CALLS, item_id=group.id, field='chat_id'):
        print('INTERFACE: edit_group(): Edit Call in Calendar')
        gcalendar.edit_event(BotUpdate(botupdate.update, botupdate.user, database.get(event.id, table=database.CALLS)[0]), botupdate)

    # EDIT SHEET
    sheet.edit_group(botupdate)

    # UPDATE DATABASE
    database.commit_group(group)
    return botupdate


def archive_group(chat_id, user_id):
    print("DATABASE: Archive Group Started")
    group = database.get(chat_id)[0]
    group.status = ARCHIVED
    # ADD GROUP INFO TO ARCHIVE
    database.commit_group(group)
    # function is not complete


def delete_group(botupdate: BotUpdate):
    print("DATABASE: Delete Group Started")
    print("DATABASE: Got Group info")
    group = botupdate.obj

    calls = database.get(group.id, table='calls', field='chat_id')
    for call in calls:
        if call != None:
            print("DATABASE: Event", call)
            gcalendar.delete_event(call.id)
            trelloc.delete_call(call.card_id)
            database.delete_record(item_id=call.id, table=database.CALLS)
        else:
            calls.remove(call)

    # DELETE CARD IN TRELLO & UPDATE CHILDREN
    # Get Children Card ids
    children = database.get(item_id=group.id, field='parent_group')
    print("DATABASE:  Children: ", children, " Type: ", type(children))
    children_cards = []
    if children[0] != None:
        for child in children:
            children_cards.append(child.card_id)
            # DELETE CHILDREN LINKS IN DATABASE
            child.parentgroup = ''
            child.is_subgroup = False
            database.commit_group(child)
    print('DATABASE: delete_group(): Children Cards: ', children_cards)

    # Get Parent
    parent_card = database.get_group_card(group.parentgroup)
    siblings = database.get_siblings(group)
    print('DATABASE: Get Parent: ', group.parentgroup,
          ' ', parent_card, ' ', siblings)

    # Delete card
    card_id = group.card_id
    trelloc.delete_group(card_id, parent_card, children_cards, siblings)
    print("DATABASE: Deleted Trello card")

    # Register Variables
    group.children = children
    group.siblings = siblings
    group.calls = calls

    # SHEET INTERFACE
    sheet.delete_group(botupdate)

    # REMOVE RECORD FROM GROUPS DATABASE
    database.delete_record(group.id, database.GROUPS)


def save_call(botupdate: BotUpdate):
    # SAVE TO CALENDAR
    call = botupdate.obj
    group_title = database.get_group_title(call.chat_id)
    group_color = database.get_group_color(call.chat_id)
    values = gcalendar.add_event(botupdate, 
        call.date, call.time, call.duration, call.title, call.description, group_title, group_color)
    print("Added call to calendar")
    event_id = values[0]
    calendar_url = values[1]

    # DURATION STRING
    seconds = int(call.duration)
    hours = seconds / 3600
    rest = seconds % 3600
    minutes = rest / 60
    duration_string = str(hours) + " Hours, " + str(minutes) + " Minutes"
    call.duration_string = duration_string

    # SAVE IN TRELLO
    trelloc.add_call(botupdate)

    # FORMAT DATE STRINGS
    date_string = datetime.strftime(call.date, '%Y/%m/%d')
    time_string = datetime.strftime(
        utils.str2datetime(str(call.time)), '%H:%M:%S')

    # SAVE EVENT IN DATABASE
    # Save Variables in Call Obj
    call.id = event_id
    call.calendar_url = calendar_url
    botupdate.card_url = 'https://trello.com/c/{}'.format(call.card_id)
    database.commit_call(call)
    print("Saved call in database")

    # SHEET INTERFACE
    sheet.save_call(botupdate)
    return botupdate


def edit_call(botupdate: BotUpdate):
    # DURATION STRING
    seconds = int(botupdate.obj.duration)
    hours = seconds / 3600
    rest = seconds % 3600
    minutes = rest / 60
    duration_string = str(hours) + " Hours, " + str(minutes) + " Minutes"
    botupdate.obj.duration_string = duration_string

    # EDIT TRELLO CARD
    trelloc.edit_call(botupdate)

    # EDIT CALENDAR EVENT
    gcalendar.edit_event(botupdate)

    # EDIT INFO IN SPREADSHEET
    sheet.edit_call(botupdate)

    # EDIT DATABASE
    database.commit_call(botupdate.obj)


def rotate_objs(first_index, direction, size=5, id='', table='groups', field='id'):
    objects = database.get(item_id=id, table=table, field=field)
    print("DATABASE: rotate_objs(): Objects: ", objects)
    if len(objects) <= size:
        return [objects, first_index]

    if direction == settings.LEFT:

        final_index = (first_index - size) % len(objects)
        if final_index < first_index:
            rotated_objs = objects[final_index:first_index]
        else:
            rotated_objs = objects[:first_index] + objects[final_index:]
            final_index = 0

    elif direction == settings.RIGHT:

        final_index = (first_index + size) % len(objects)
        if final_index < first_index:
            rotated_objs = objects[first_index - 1:final_index]
        else:
            rotated_objs = objects[final_index - 1:] + objects[:first_index]
            final_index = 0

    print("DATABASE - Rotate Groups: ", rotated_objs,
          " | Final Index: ", final_index)
    return [rotated_objs, final_index]


def feedback(feedback):
    print('INTERFACE: - CREATE ISSUE - ')
    # ADD ISSUE IN GITHUB
    feedback = githubc.create_issue(feedback)
    return feedback


def authenticate(update, context, state, only_chats=True):
    """Authenticates user before execiting commands. 
    If user is not registerred in any web of trust, the function will see weather the current 
    group is activated and will add the user to the database accordingly.
    :param update: Telegram Update
    :param botupdate: BotUpdate - Do not include in the first step of a ConversationHandler.
    :param state: 0-> Authenticates User | 1-> Makes sure user is the same

    :returns: Authenticated BotUpdate or None if user doesn't have permission
    :rtype: BotUpdate
    """
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if state == 0:
        # First Conversation Authentication
        user = database.get(table=database.USERS, item_id=user_id)[0]
        if user:
            # User is registerred in web of trust
            botupdate = BotUpdate(update, update.effective_user)
            if only_chats and user.id == chat_id:
                # Command run in private chat

                return None
            else:
                return botupdate
        else:
            # User is not registerred in web of trust
            group = database.get(chat_id)[0]
            if group:
                # Group chat is activated
                # Register user in web of trust
                user = User(user_id, user.first, user.last, username, group.activator_id)
                database.commit_user(user)
                botupdate = BotUpdate(update, update.effective_user)
                return botupdate
            else:
                # Group chat is not activated
                return None
    else:
        # Make sure user is the same who started the conversation
        botupdate = utils.load_pkl('edit_group', chat_id, user_id)
        if botupdate:
            return botupdate
        else:
            return None


def send_message(update, context, text):
    if update.callback_query:
        # Update has callbackquery
        message = update.callback_query.edit_text(text, parse_mode=ParseMode.HTML)
        return message
    else:
        message = update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return message
