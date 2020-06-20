from datetime import datetime
import sqlite3
from fff_automation.modules import utils, settings, encryption
from fff_automation.classes.call import Call
from fff_automation.classes.group import Group
from fff_automation.classes.user import User
import ast


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
            activator_id,
            activator_name
            ) VALUES (:id, :card_id, :title, :category, :restriction, :region, :platform, :color, :is_subgroup, :parent_group, :purpose, :onboarding, :date, :status, :activator_id, :activator_name)''',
                  {'id': encryption.encrypt(obj.id),
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
            'id': encryption.encrypt(obj.id),
            'chat_id': encryption.encrypt(obj.chat_id),
            'card_id': encryption.encrypt(obj.card_id),
            'title': encryption.encrypt(obj.title),
            'date': obj.date,
            'time': obj.time,
            'duration': obj.duration,
            'description': obj.description, 'agenda_link': encryption.encrypt(obj.agenda_link), 'calendar_url': encryption.encrypt(obj.calendar_url),
            'link': encryption.encrypt(obj.link),
            'user_id': encryption.encrypt(obj.user_id),
            'status': obj.status, })
    conn.commit()
    conn.close()


def commit_user(obj):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    if isinstance(obj, User):
        c.execute("INSERT OR REPLACE INTO users(id, first, last, username, activator_id) VALUES (:id, :first, :last, :username, :activator_id)", {
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
    if item_id == '':
        sqlstr = 'SELECT * FROM {}'.format(table)
        c.execute(sqlstr)
    else:
        if encrypt:
            item_id = encryption.encrypt(item_id)
        sqlstr = "SELECT * FROM {} WHERE {}=?".format(table, field)
        c.execute(sqlstr, (item_id,))
    results = c.fetchall()
    conn.close()
    print('DATABASE: RESULT: ', results)
    if results == []:
        print('DATABASE: No results where found from query: ', item_id)
        return [None]
    if not isinstance(results[0], tuple):
        results = [results]
    items = []
    for result in results:
        if table == 'groups':
            obj = Group(
                id=encryption.decrypt(result[0]),
                card_id=encryption.decrypt(result[1]),
                title=result[2],
                category=result[3],
                restriction=result[4],
                region=result[5],
                platform=result[6],
                color=result[7],
                is_subgroup=ast.literal_eval(result[8]),
                parentgroup=encryption.decrypt(result[9]),
                purpose=result[10],
                onboarding=result[11],
                date=result[12],
                status=result[13],
                activator_id=encryption.decrypt(result[14]),
                activator_name=encryption.decrypt(result[15])
            )
            items.append(obj)
        elif table == 'calls':
            obj = Call(
                id=encryption.decrypt(result[0]),
                chat_id=encryption.decrypt(result[1]),
                card_id=encryption.decrypt(result[2]),
                title=result[3],
                date=result[4],
                time=result[5],
                duration=result[6],
                description=result[7],
                agenda_link=encryption.decrypt(result[8]),
                calendar_url=encryption.decrypt(result[9]),
                link=encryption.decrypt(result[10]),
                user_id=encryption.decrypt(result[11]),
                status=result[12],
            )
            items.append(obj)
        elif table == 'users':
            obj = User(
                id=encryption.decrypt(result[0]),
                first=encryption.decrypt(result[1]),
                last=encryption.decrypt(result[2]),
                username=encryption.decrypt(result[3]),
                activator_id=encryption.decrypt(result[4])
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
