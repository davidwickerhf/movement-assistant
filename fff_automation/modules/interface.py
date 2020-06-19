import gspread
import os
import json
import pickle
from oauth2client.service_account import ServiceAccountCredentials
from fff_automation.modules import gcalendar, trelloc, settings, utils, sheet, database, githubc
from fff_automation.classes.group import Group
from fff_automation.classes.call import Call
from fff_automation.classes.user import User
from datetime import datetime

REGULAR, ARCHIVED, DELETED = range(3)


def save_group(group):
    # REGISTER ALL USERS
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
            activator_id=group.user_id
        )
        database.commit_user(obj)

        if member.status in ('creator', 'administrator'):
            user = member.user
            admins_string += "{}; ".format(user.name)

    admins_string = admins_string[:-2]
    group.admins_string = admins_string
    print("INTERFACE: Got Admins")

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
    card_info = trelloc.add_group(group)
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
    sheet.save_group(group)
    return card_url


def edit_group(group):
    print('INTERFACE: edit_group()')
    # EDIT TRELLO CARD
    group.children = database.get(group.id, field='parent_group')
    group.old_group = database.get(group.id)[0]
    group.old_group.siblings = database.get_siblings(group.old_group)
    group.siblings = database.get_siblings(group)
    
    trelloc.edit_group(group)

    # EDIT SHEET
    sheet.edit_group(group)

    # UPDATE DATABASE
    database.commit_group(group)
    return group


def archive_group(chat_id, user_id):
    print("DATABASE: Archive Group Started")
    group = database.get(chat_id)[0]
    group.status = ARCHIVED
    # ADD GROUP INFO TO ARCHIVE
    database.commit_group(group)
    # function is not complete


def delete_group(group):
    print("DATABASE: Delete Group Started")
    group = database.get(item_id=group.id)[0]
    print("DATABASE: Got Group info")

    calls = database.get(group.id, table='calls', field='chat_id')
    for call in calls:
        if call != None:
            print("DATABASE: Event", call)
            gcalendar.delete_event(call.id)
            trelloc.delete_call(call.card_id)
            database.delete_record(item_id=call.id, table='calls')
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
    try:
        sheet.delete_group(group)
    except:
        print('INTERFACE: Group non existent in Sheet')

    # REMOVE RECORD FROM GROUPS DATABASE
    database.delete_record(group.id, 'groups')


def save_call(call):
    # SAVE TO CALENDAR
    group_title = database.get_group_title(call.chat_id)
    group_color = database.get_group_color(call.chat_id)
    values = gcalendar.add_event(
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
    values = trelloc.add_call(call)
    trello_url = values[1]
    card_id = values[0]

    # FORMAT DATE STRINGS
    date_string = datetime.strftime(call.date, '%Y/%m/%d')
    time_string = datetime.strftime(
        utils.str2datetime(str(call.time)), '%H:%M:%S')

    # SAVE EVENT IN DATABASE
    # Save Variables in Call Obj
    call.id = event_id
    call.date = date_string
    call.time = time_string
    call.card_id = card_id
    call.calendar_url = calendar_url
    call.card_url = 'https://trello.com/c/{}'.format(call.card_id)
    database.commit_call(call)
    print("Saved call in database")

    # SHEET INTERFACE
    sheet.save_call(call)
    return [calendar_url, trello_url]


def rotate_groups(first_index, direction, size=5):
    groups = database.get()
    print("DATABASE: rotate_groups(): Groups: ", groups)
    if len(groups) <= size:
        return [groups, first_index]

    if direction == 0:

        final_index = (first_index - size) % len(groups)
        if final_index < first_index:
            rotated_groups = groups[final_index:first_index]
        else:
            rotated_groups = groups[:first_index] + groups[final_index:]
            final_index = 0

    elif direction == 1:

        final_index = (first_index + size) % len(groups)
        if final_index < first_index:
            rotated_groups = groups[first_index - 1:final_index]
        else:
            rotated_groups = groups[final_index - 1:] + groups[:first_index]
            final_index = 0

    print("DATABASE - Rotate Groups: ", rotated_groups,
          " | Final Index: ", final_index)
    return [rotated_groups, final_index]


def feedback(feedback):
    print('INTERFACE: - CREATE ISSUE - ')
    # ADD ISSUE IN GITHUB
    feedback = githubc.create_issue(feedback)
    return feedback
