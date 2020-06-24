from datetime import datetime
import sqlite3
from fff_automation.modules import utils, settings, encryption
from fff_automation.classes.call import Call
from fff_automation.classes.group import Group
from fff_automation.classes.user import User
import ast
import uuid

GROUPS = 'groups'
CALLS = 'calls' 
USERS = 'users'


def get_group_title(group_id):
    print("DATABASE: get_group_title()")
    obj = get(group_id)[0]
    group_title = obj.title
    return group_title


def get_group_color(group_id):
    print("DATABASE: get_group_color()")
    obj = get(group_id)[0]
    group_color = obj.color
    return group_color


def get_group_card(group_id):
    print("DATABASE: get_group_card()")
    obj = get(group_id)[0]
    if obj == None:
        return None
    card_id = obj.card_id
    return card_id


def get_siblings(obj):
    print('DATABASE: Query for ', obj.parentgroup)
    siblings = get(item_id=obj.parentgroup, field='parent_group')
    if siblings[0] == None:
        print('DATABASE: get_siblings(): no siblings')
        return []
    for sibling in siblings:
        if sibling.id == obj.id:
            siblings.remove(sibling)
    print('DATABASE: get_siblings(): ', siblings)
    return siblings


def commit_group(obj):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    obj.key = get_key(obj.id, GROUPS)
    if not obj.key:
        loop = True
        while loop:
            obj.key = uuid.uuid4().hex[:6].upper()
            c.execute('''SELECT * FROM groups WHERE key=?''', (obj.key,))
            results = c.fetchall()
            if results in [None, []]:
                loop = False
    if isinstance(obj, Group):
        c.execute('''INSERT OR REPLACE INTO groups(
            key,
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
            activator_id,
            activator_name
            ) VALUES (:key, :id, :card_id, :title, :category, :restriction, :region, :platform, :color, :is_subgroup, :parent_group, :purpose, :onboarding, :date, :status, :activator_id, :activator_name)''',
                  {'key': obj.key,
                   'id': encryption.encrypt(obj.id),
                   'card_id': encryption.encrypt(obj.card_id),
                   'title': obj.title,
                   'category': obj.category,
                   'restriction': obj.restriction,
                   'region': obj.region,
                   'platform': obj.platform,
                   'color': obj.color,
                   'is_subgroup': str(obj.is_subgroup),
                   'parent_group': encryption.encrypt(obj.parentgroup),
                   'purpose': obj.purpose,
                   'onboarding': obj.onboarding,
                   'date': obj.date,
                   'status': obj.status,
                   'activator_id': encryption.encrypt(obj.activator_id),
                   'activator_name': encryption.encrypt(obj.activator_name)})
    conn.commit()
    conn.close()


def commit_call(obj):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    obj.key = get_key(obj.id, CALLS)
    if not obj.key:
        loop = True
        while loop:
            obj.key = uuid.uuid4().hex[:6].upper()
            c.execute('''SELECT * FROM calls WHERE key=?''', (obj.key,))
            results = c.fetchall()
            if results in [None, []]:
                loop = False
    if isinstance(obj, Call):
        c.execute('''INSERT OR REPLACE INTO calls(
            key,
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
            status) VALUES (:key, :id, :chat_id, :card_id, :title, :date, :time, :duration, :description, :agenda_link, :calendar_url, :link, :user_id, :status)''', {
            'key': obj.key,
            'id': encryption.encrypt(obj.id),
            'chat_id': encryption.encrypt(obj.chat_id),
            'card_id': encryption.encrypt(obj.card_id),
            'title': obj.title,
            'date': obj.date,
            'time': obj.time,
            'duration': obj.duration,
            'description': obj.description, 'agenda_link': encryption.encrypt(obj.agenda_link), 'calendar_url': encryption.encrypt(obj.calendar_url),
            'link': encryption.encrypt(obj.link),
            'user_id': encryption.encrypt(obj.user_id),
            'status': obj.status})
    conn.commit()
    conn.close()


def commit_user(obj):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    obj.key = get_key(obj.id, USERS)
    if not obj.key:
        loop = True
        while loop:
            obj.key = uuid.uuid4().hex[:6].upper()
            c.execute('''SELECT * FROM users WHERE key=?''', (obj.key,))
            results = c.fetchall()
            if results in [None, []]:
                loop = False
    if isinstance(obj, User):
        c.execute("INSERT OR REPLACE INTO users(id, first, last, username, activator_id) VALUES (:id, :first, :last, :username, :activator_id)", {
            'key': obj.key,
            'id': encryption.encrypt(obj.id),
            'first': encryption.encrypt(obj.first),
            'last': encryption.encrypt(obj.last),
            'username': encryption.encrypt(obj.username),
            'activator_id': encryption.encrypt(obj.activator_id)})
    conn.commit()
    conn.close()


def get(item_id='', table='groups', field='id', encrypt=True):
    """
    Return a list of group/call/user objects that match the query of the item_id.
    Returns [None] if there is no result
    """
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    sqlstr = "SELECT * FROM {}".format(table)
    c.execute(sqlstr)
    results = c.fetchall()
    conn.close()
    
    if results not in [None, []]:
        if not isinstance(results[0], tuple):
            results = [results]

    items = []
    for result in results:
        if table == 'groups':
            obj = Group(
                key=result[0],
                id=encryption.decrypt(result[1]),
                card_id=encryption.decrypt(result[2]),
                title=result[3],
                category=result[4],
                restriction=result[5],
                region=result[6],
                platform=result[7],
                color=result[8],
                is_subgroup=ast.literal_eval(result[9]),
                parentgroup=encryption.decrypt(result[10]),
                purpose=result[11],
                onboarding=result[12],
                date=result[13],
                status=result[14],
                activator_id=encryption.decrypt(result[15]),
                activator_name=encryption.decrypt(result[16])
            )
            if obj.is_subgroup:
                obj.parentgroup = int(obj.parentgroup)
        elif table == 'calls':
            obj = Call(
                key=result[0],
                id=encryption.decrypt(result[1]),
                chat_id=encryption.decrypt(result[2]),
                card_id=encryption.decrypt(result[3]),
                title=result[4],
                date=result[5],
                time=result[6],
                duration=result[7],
                description=result[8],
                agenda_link=encryption.decrypt(result[9]),
                calendar_url=encryption.decrypt(result[10]),
                link=encryption.decrypt(result[11]),
                activator_id=encryption.decrypt(result[12]),
                status=result[13],
            )
        elif table == 'users':
            obj = User(
                key=result[0],
                id=encryption.decrypt(result[1]),
                first=encryption.decrypt(result[2]),
                last=encryption.decrypt(result[3]),
                username=encryption.decrypt(result[4]),
                activator_id=encryption.decrypt(result[5])
            )

        if field == 'id':
            check = obj.id
            print('DATABASE: get(): check: ', check, ' ', type(check))
        elif field == 'parent_group':
            check = obj.parentgroup
        elif field == 'activator_id':
            check = obj.activator_id
        elif field == 'chat_id':
            check = obj.chat_id

        if item_id == '' or check == item_id:
            items.append(obj)

    if items == []:
        print('DATABASE: No results where found from query')
        items = [None]

    return items


def get_key(id, table):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    sqlstr = 'SELECT * FROM {}'.format(table)
    c.execute(sqlstr)
    results = c.fetchall()
    conn.close()

    for item in results:
        if encryption.decrypt(item[1]) == id:
             return item[0]
    return None


def delete_record(item_id, table):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    key = get_key(item_id, table)
    sqlstr = "DELETE FROM {table} WHERE key=?".format(table=table)
    c.execute(sqlstr, (key,))
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
