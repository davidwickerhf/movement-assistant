import gspread
import os
import json
import pickle
from oauth2client.service_account import ServiceAccountCredentials
from fff_automation.modules import gcalendar, trelloc, settings, utils, sheet
from fff_automation.classes.group import Group
from fff_automation.classes.call import Call
from fff_automation.classes.user import User
from datetime import datetime
import sqlite3

REGULAR, ARCHIVED, DELETED = range(3)


def save_group(group):
    # REGISTER ALL USERS
    users = []
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
        commit_user(obj)

    # GET GROUP ADMINS
    admins_string = ""
    for chatMemeber in group.users:
        print("DATABASE: Getting group admins")
        if chatMemeber.status in ['creator', 'administrator']:
            user = chatMemeber.user
            admins_string += "{}; ".format(user.name)

    admins_string = admins_string[:-2]
    print("DATABASE: Got Admins")

    # GET RANDOM CALENDAR COLOR:
    color_id = utils.get_random_event_color()
    print("DATABASE: Got Group Color")

    # CREATE TRELLO CARD
    if group.is_subgroup:
        parent_card = get_group_card(group.parentgroup)
        print("DATABASE: Got parent card ", parent_card)
    else:
        parent_card = ""
        print("DATABASE: No parent")
    card_info = trelloc.add_group(title=group.title, admins=admins_string, purpose=group.purpose, onboarding=group.onboarding, platform=group.platform,
                                  region=group.region, group_type=group.category, restriction=group.restriction, is_subgroup=group.is_subgroup, parentgroup_id=parent_card, date=group.date)
    card_id = card_info[0]
    card_url = card_info[1]
    print("DATABASE: Got Trello Card Info")

    # SAVE GROUP IN DATABASE
    # Save Variables in Group Obj
    group.card_id = card_id
    group.color = color_id
    group.is_subgroup = str(group.is_subgroup)
    commit_group(group)
    print("DATABASE: Saved group")

    # SAVE IN KUMA BOARD

    # LOG ACTION
    sheet.log(str(utils.now_time()), group.user_id,
              'ACTIVATE GROUP', group.title)
    return card_url


def update_group(chat_id, title, admins, category="", level="",
                 platform="", purpose="", mandate="", onboarding="", link=""):
    try:
        row = find_row_by_id(chat_id)[0]
    except:
        save_group(chat_id, title, category, level,
                   admins, platform, purpose, mandate, onboarding, link)
    # function is not complete


def archive_group(chat_id, user_id):
    print("DATABASE: Archive Group Started")
    group = find_row_by_id(chat_id)[0]
    group.status = ARCHIVED
    # ADD GROUP INFO TO ARCHIVE
    commit_group(group)
    # function is not complete


def delete_group(chat_id, user_id):
    print("DATABASE: Delete Group Started")
    group = find_row_by_id(item_id=chat_id)[0]
    print("DATABASE: Got Group info")

    calls = find_row_by_id(chat_id, table='calls', field='chat_id')
    for call in calls:
        print("DATABASE: Event", call)
        gcalendar.delete_event(call.id)
        trelloc.delete_call(call.card_id)
        delete_record(item_id=call.id, table='calls')

    # DELETE CARD IN TRELLO
    # Get Children Card ids
    children = find_row_by_id(item_id=chat_id, field='parent_group')
    print("DATABASE:  Children: ", children, " Type: ", type(children))
    children_cards = []
    if children[0] != None:
        for child in children:
            children_cards.append(child.card_id)
            # DELETE CHILDREN LINKS IN DATABASE
            child.parentgroup = ''
            child.is_subgroup = 'FALSE'
            commit_group(child)
    print('DATABASE: delete_group(): Children Cards: ', children_cards)

    # Get Parent
    parent_id = group.parentgroup
    parent_card = get_group_card(parent_id)
    siblings = find_row_by_id(item_id=parent_id, field='parent_group')
    for sibling in siblings:
        if sibling.id == chat_id:
            siblings.remove(sibling)
    print('DATABASE: Get Parent: ', parent_id, ' ', parent_card, ' ', siblings)

    # Delete card
    card_id = group.card_id
    trelloc.delete_group(card_id, parent_card, children_cards, siblings)
    print("DATABASE: Deleted Trello card")

    # REMOVE RECORD FROM GROUPS DATABASE
    delete_record(chat_id, 'groups')

    # LOG ACTION
    sheet.log(str(utils.now_time()), user_id, 'DELETE GROUP', group.title)


def save_call(call):
    # SAVE TO CALENDAR
    group_title = get_group_title(call.chat_id)
    group_color = get_group_color(call.chat_id)
    values = gcalendar.add_event(
        call.date, call.time, call.duration, call.title, call.description, group_title, group_color)
    print("Added call to calendar")
    event_id = values[0]
    calendar_url = values[1]

    # SAVE IN TRELLO
    values = trelloc.add_call(call.title, get_group_title(group_id=call.chat_id), get_group_card(
        group_id=call.chat_id), call.date, call.time, call.duration, call.description, call.agenda_link, calendar_url, call.username)
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
    commit_call(call)
    print("Saved call in database")

    sheet.log(str(utils.now_time()), call.user_id, 'NEW CALL', group_title)
    return [calendar_url, trello_url]


def get_group_title(group_id):
    print("DATABASE: get_group_title()")
    obj = find_row_by_id(group_id)[0]
    group_title = obj.title
    return group_title


def get_group_color(group_id):
    print("DATABASE: get_group_color()")
    obj = find_row_by_id(group_id)[0]
    group_color = obj.color
    return group_color


def get_group_card(group_id):
    print("DATABASE: get_group_card()")
    obj = find_row_by_id(group_id)[0]
    if obj == None:
        return None
    card_id = obj.card_id
    return card_id


def rotate_groups(first_index, direction, size=5):
    groups = find_row_by_id()
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


def commit_group(obj):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    if isinstance(obj, Group):
        c.execute('''INSERT OR REPLACE INTO groups(
            id,
            card_id,
            title,
            category,
            restriction,
            region,
            platform,
            color,
            is_subgroup,
            parent_group,
            purpose,
            onboarding,
            date,
            status,
            user_id
            ) VALUES (:id, :card_id, :title, :category, :restriction, :region, :platform, :color, :is_subgroup, :parent_group, :purpose, :onboarding, :date, :status, :user_id)''',
                  {'id': obj.id,
                   'card_id': obj.card_id,
                   'title': obj.title,
                   'category': obj.category,
                   'restriction': obj.restriction,
                   'region': obj.region,
                   'platform': obj.platform,
                   'color': obj.color,
                   'is_subgroup': obj.is_subgroup,
                   'parent_group': obj.parentgroup,
                   'purpose': obj.purpose,
                   'onboarding': obj.onboarding,
                   'date': obj.date,
                   'status': obj.status,
                   'user_id': obj.user_id})
    conn.commit()
    conn.close()


def commit_call(obj):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    if isinstance(obj, Call):
        c.execute('''INSERT OR REPLACE INTO calls(
            id,
            chat_id,
            card_id,
            title,
            date,
            time,
            duration,
            description,
            agenda_link,
            calendar_url,
            link,
            user_id,
            status) VALUES (:id, :chat_id, :card_id, :title, :date, :time, :duration, :description, :agenda_link, :calendar_url, :link, :user_id, :status)''', {
            'id': obj.id,
            'chat_id': obj.chat_id,
            'card_id': obj.card_id,
            'title': obj.title,
            'date': obj.date,
            'time': obj.time,
            'duration': obj.duration,
            'description': obj.description, 'agenda_link': obj.agenda_link, 'calendar_url': obj.calendar_url,
            'link': obj.link,
            'user_id': obj.user_id,
            'status': obj.status, })
    conn.commit()
    conn.close()


def commit_user(obj):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    if isinstance(obj, User):
        c.execute("INSERT OR REPLACE INTO users(id, first, last, username, activator_id) VALUES (:id, :first, :last, :username, :activator_id)", {
            'id': obj.id,
            'first': obj.first,
            'last': obj.last,
            'username': obj.username,
            'activator_id': obj.activator_id})
    conn.commit()
    conn.close()


def find_row_by_id(item_id='', table='groups', field='id'):
    """
    Return a list of group/call/user objects that match the query of the item_id.
    Returns [None] if there is no result
    """
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    if item_id == '':
        sqlstr = 'SELECT * FROM {}'.format(table)
        c.execute(sqlstr)
    else:
        sqlstr = "SELECT * FROM {} WHERE {}={}".format(table, field, item_id)
        c.execute(sqlstr)
    results = c.fetchall()
    conn.close()
    print('DATABASE: RESULT: ', results)
    if results == []:
        return [None]
    if not isinstance(results[0], tuple):
        results = [results]
    items = []
    for result in results:
        if table == 'groups':
            obj = Group(
                id=result[0],
                card_id=result[1],
                title=result[2],
                category=result[3],
                restriction=result[4],
                region=result[5],
                platform=result[6],
                color=result[7],
                is_subgroup=result[8],
                parentgroup=result[9],
                purpose=result[10],
                onboarding=result[11],
                date=result[12],
                status=result[13],
                user_id=result[14]
            )
            items.append(obj)
        elif table == 'calls':
            obj = Call(
                id=result[0],
                chat_id=result[1],
                card_id=result[2],
                title=result[3],
                date=result[4],
                time=result[5],
                duration=result[6],
                description=result[7],
                agenda_link=result[8],
                calendar_url=result[9],
                link=result[10],
                user_id=result[11],
                status=result[12],
            )
            items.append(obj)
        elif table == 'users':
            obj = User(
                id=result[0],
                first=result[1],
                last=result[2],
                username=result[3],
                activator_id=result[4]
            )
            items.append(obj)
    return items


def delete_record(item_id, table, field='id'):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    sqlstr = "DELETE FROM {table} WHERE {field}=?".format(
        table=table, field=field)
    c.execute(sqlstr, (item_id,))
    conn.commit()
    conn.close()


def setup():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    users = c.fetchone()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    groups = c.fetchone()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    calls = c.fetchone()
    conn.close()
    if None in (users, groups, calls):
        print('DATABASE: Setting Up Database')
        settings.set_database(users, groups, calls)
    else:
        print('DATABASE: DB already set up')


setup()
