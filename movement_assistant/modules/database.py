from datetime import datetime
from movement_assistant.modules import encryption
from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from movement_assistant.modules import utils, settings
from movement_assistant.classes.organisation import Organisation
from movement_assistant.classes.call import Call
from movement_assistant.classes.group import Group
from movement_assistant.classes.user import User
import ast
import uuid

GROUPS = 'groups'
CALLS = 'calls' 
USERS = 'users'

Base = declarative_base()

memberships = Table(
    'memberships', Base.metadata,
    Column('member_id', Integer, ForeignKey('member.id')),
    Column('organisation_id', Integer, ForeignKey('organisation.id')))


class DOrganisation(Base):
    __tablename__ = 'organisation'
    id = Column(Integer, primary_key=True)
    name = Column(String(30))
    description = Column(String(500))
    # Ties with other tables
    groups = relationship('Group', backref='org')
    members = relationship('Member', secondary=memberships, back_populates='organisations')


class DGroup(Base):
    __tablename__ = 'group'
    id = Column(Integer, primary_key=True)
    card_id = Column(String(60), nullable=False)
    title = Column(String(25), nullable=False)
    category = Column(String(20), nullable=False)
    restriction = Column(String(20), nullable=False)
    region = Column(String(20), nullable=False)
    platform = Column(String(20), nullable=False)
    color = Column(Integer, nullable=False)
    purpose = Column(String(350), nullable=True)
    onboarding = Column(String(350), nullable=True)
    date = Column(String(20), nullable=False)
    status = Column(Integer, nullable=False)
    is_subgroup = Column(String(20), nullable=False)
    # Ties with other tables
    parentgroup = Column(Integer, ForeignKey('group.id'))
    activator = Column(Integer, ForeignKey('member.id'))
    organisation = Column(Integer, ForeignKey('organisation.id'))
    subgroups = relationship('Group', backref='parentgroup')
    calls = relationship('Call', backref='group')


class DCall(Base):
    __tablename__ = 'call'
    id = Column(Integer, primary_key=True)
    group = Column(Integer, ForeignKey('group.id'))
    card_id = Column(String(60), nullable=False)
    title = Column(String(25), nullable=False)
    date = Column(String(30), nullable=False)
    time = Column(String(20), nullable=False)
    duration = Column(String(20), nullable=False)
    description = Column(String(350), nullable=True)
    agenda_link = Column(String(350), nullable=True)
    calendar_url = Column(String(350), nullable=False)
    link = Column(String(350), nullable=True)
    activator = Column(Integer, ForeignKey('member.id'))
    status = Column(Integer, nullable=False)


class DMember(Base):
    __tablename__ = 'member'
    id = Column(Integer, primary_key=True)
    first = Column(String(25), nullable=True)
    last = Column(String(25), nullable=False)
    username = Column(String(25), nullable=False)
    activator = Column(Integer, ForeignKey('member.id'))
    organisations = relationship
    activated_groups = relationship('Group', backref='activator')
    activated_calls = relationship('Call', backref='activator')
    activated_members = relationship('Member', backref='activator')
    organisations = relationship('Organisation', secondary=memberships,back_populates='members')


def setup():
    engine = create_engine('sqlite:///data.db')
    Base.metadata.create_all(engine)


def addObj(obj):
    """
    Adds objects to the database depending on the obj type.
    Assumes member objects are saved before other objects.
    """
    engine = create_engine('sqlite:///data.db')
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    # create new object based on obj type
    if isinstance(obj, Group):
        # object is a group
        dobj = DGroup(
            card_id=encrypt(obj.card_id),
            title=obj.title,
            category=obj.category,
            restriction=obj.restriction,
            region=obj.region,
            platform=obj.platform,
            color=obj.color,
            purpose=obj.purpose,
            onboarding=obj.onboarding,
            date=str(obj.date),
            status=obj.status,
            is_subgroup=str(obj.is_subgroup),
            parentgroup=obj.parentgroup,
            activator=encrypt(obj.activator_id)
        )
    elif isinstance(obj, Call):
        # object is a call
        
    elif isinstance(obj, Organisation):
        # object is org
    elif isinstance(obj, Member):
        # object is member
    else:
        raise ValueError
    session.add(dobj)
    session.commit()
    
    


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
            activator_id,
            status) VALUES (:key, :id, :chat_id, :card_id, :title, :date, :time, :duration, :description, :agenda_link, :calendar_url, :link, :activator_id, :status)''', {
            'key': obj.key,
            'id': encryption.encrypt(obj.id),
            'chat_id': encryption.encrypt(obj.chat_id),
            'card_id': encryption.encrypt(obj.card_id),
            'title': obj.title,
            'date': datetime.strftime(obj.date, '%Y/%m/%d'),
            'time':  datetime.strftime(utils.str2datetime(str(obj.time)), '%H:%M:%S'),
            'duration': obj.duration,
            'description': obj.description, 'agenda_link': encryption.encrypt(obj.agenda_link), 'calendar_url': encryption.encrypt(obj.calendar_url),
            'link': encryption.encrypt(obj.link),
            'activator_id': encryption.encrypt(obj.activator_id),
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
        c.execute("INSERT OR REPLACE INTO users(key, id, first, last, username, activator_id) VALUES (:key, :id, :first, :last, :username, :activator_id)", {
            'key': obj.key,
            'id': encryption.encrypt(obj.id),
            'first': encryption.encrypt(obj.first),
            'last': encryption.encrypt(obj.last),
            'username': encryption.encrypt(obj.username),
            'activator_id': encryption.encrypt(obj.activator_id)})
    conn.commit()
    conn.close()


def get(item_id='', table='groups', field='id'):
    """Return a list of objects that match the query.
    Returns [None] if no object matches the query.
    :param item_id: The id to look for. If no id is provided, a list of all available items in the specified table will be returned
    :param table: the Database table to look into
    :field: the field to match with the id. Can be 'id', 'key', 'parent_group', 'activator_id', 'chat_id'
    :returns: List of objects or [None]
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
                date=utils.str2date(result[13]),
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
                date=utils.str2date(result[5]),
                time=utils.str2time(result[6]),
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
        elif field == 'key':
            check = obj.key
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
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orgs'")
    calls = c.fetchone()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    users = c.fetchone()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='groups'")
    groups = c.fetchone()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='calls'")
    calls = c.fetchone()
    conn.close()
    if None in (users, groups, calls):
        print('DATABASE: Setting Up Database')
        settings.set_database(users, groups, calls)
    else:
        print('DATABASE: DB already set up')
