import os
import emoji
from fff_automation.modules import utils
from trello import TrelloClient
from fff_automation.modules import settings, database
import requests
import json
import re


TRELLO_KEY = settings.get_var('TRELLO_KEY')
print("TRELLOC: Trello Key: ", TRELLO_KEY)
TRELLO_TOKEN = settings.get_var('TRELLO_TOKEN')
print("TRELLOC: Trello Token: ", TRELLO_TOKEN)

client = TrelloClient(
    api_key=TRELLO_KEY,
    token=TRELLO_TOKEN,
)

if settings.get_var('TRELLO_BOARD_ID') == -1:
    # Creating new board
    print("TERLLOC: No Past Trello Id found")
    settings.set_trello(client, TRELLO_KEY, TRELLO_TOKEN)
else:
    # Board is indicated, saving lists and labels ids as config vars.
    # Cicle through the lists
    # Add the lists ids to the env. file
    print("TRELLOC: Initiating Config Vars. Board Exists")
    # Get lists from Trello
    lists = client.get_board(
        board_id=settings.get_var('TRELLO_BOARD_ID')).all_lists()
    lists = lists[3:]

    lists_dict = {}
    for num, trellolist in enumerate(lists):
        lists_dict[num] = trellolist.id
    settings.set_var('lists', lists_dict)

    # Cicle through the labels
    # Remove the labels without name
    # Add the lables to env. file
    labels = client.get_board(board_id=settings.get_var(
        'TRELLO_BOARD_ID')).get_labels()
    labels_dict = {}
    remove = []
    for num, label in enumerate(labels):
        if label.name == '':
            remove.append(label)
    for label in remove:
        labels.remove(label)
    for label in labels:
        for num, index in enumerate(settings.label_order):
            if index in label.name:
                labels_dict[num + 7] = label.id
    settings.set_var('labels', labels_dict)


board_id = settings.get_var('TRELLO_BOARD_ID')
board = client.get_board(board_id=board_id)

# LISTS (COLUMNS) IN TRELLO BOARD
planned_calls_list = board.get_list(
    settings.get_var(settings.TL_PLANNEDCALLS, 'lists'))
dg_list = board.get_list(settings.get_var(
    settings.TL_DG, 'lists'))
wg_list = board.get_list(settings.get_var(
    settings.TL_WG, 'lists'))
projects_list = board.get_list(
    settings.get_var(settings.TL_IP, 'lists'))
past_calls_list = board.get_list(
    settings.get_var(settings.TL_PASTCALLS, 'lists'))
archive_list = board.get_list(settings.get_var(settings.TL_ARCHIVE, 'lists'))

# LABELS IDs -  accessed by bots
upcoming_id = settings.get_var(settings.TB_UPCOMING, 'labels')
past_call_label_id = settings.get_var(settings.TB_PAST, 'labels')
# Restriction labels ids
restrictions = {'Open': settings.get_var(settings.TB_OPEN, 'labels'),
                "Restricted": settings.get_var(settings.TB_RESTRICTED, 'labels'),
                "Closed": settings.get_var(settings.TB_CLOSED, 'labels')}
# Region labels ids
regions = {"Global": settings.get_var(settings.TB_GLOBAL, 'labels'),
           "Europe": settings.get_var(settings.TB_EUROPE, 'labels'),
           "South America": settings.get_var(settings.TB_SOUTHAMERICA, 'labels'),
           "North America": settings.get_var(settings.TB_NORTHAMERICA, 'labels'),
           "Africa": settings.get_var(settings.TB_AFRICA, 'labels'),
           "Asia": settings.get_var(settings.TB_ASIA, 'labels'),
           "Oceania": settings.get_var(settings.TB_OCEANIA, 'labels')}

WORKING_GROUP = "Working Group"
DISCUSSION_GROUP = "Discussion Group"
PROJECT = "Project/Event"


def add_group(group):
    # SET LABELS
    labels = []
    if group.region != "":
        print("TRELLOC: Region Id: ", group.region)
        labels.append(client.get_label(regions[group.region], board_id))
    if group.restriction != "":
        print("TRELLOC: Restriction Id: ", group.restriction)
        labels.append(client.get_label(
            restrictions[group.restriction], board_id))
    print("TRELLO: Got labels: ", labels)

    group_list = ""
    # SELECT LIST
    if group.category == WORKING_GROUP:
        group_list = wg_list
    elif group.category == DISCUSSION_GROUP:
        group_list = dg_list
    elif group.category == PROJECT:
        group_list = projects_list
    print("TRELLO: Got list")

    # SET DESCRIPTION
    description = "**INTERNATIONAL {}**\n **Purpose: **{}\n\n**Onboarding:** {}\n\n**Group Category:** {}\n**Group Region:** {}\n**Group Platform:** {}\n**Group Admins:** {}\n\n**Registered on:** {}".format(
        group.category.upper(), group.purpose, group.onboarding, group.category, group.region, group.platform, group.admin_string, group.date)

    # ATTACH PARENT CARD LINK TO DESCRIPTION
    if group.is_subgroup:
        print("TRELLOC: Parent ID:", group.parentgroup)
        parentcard_id = database.get_group_card(group.parentgroup)
        print('TRELLOC: Parent Card: ', parentcard_id)
        description = description + \
            "\n\n**Parent Group:** https://trello.com/c/{}".format(
                str(parentcard_id))
    print("TRELLO: Set description")

    # SAVE CARD AND GET ID
    newcard = group_list.add_card(
        name=group.title, desc=description, labels=labels, position="bottom")
    print("TRELLO: Saved Card: ", newcard)
    print("TRELLO: Card type: ", type(newcard))

    # ATTACH CARD TO PARENT DESCRIPTION
    if group.is_subgroup:
        print("TRELLOC: add_group(): Parent Group Card Id: ", parentcard_id)
        parentgroup_card = get_card(parentcard_id)
        print("TRELLOC: add_group(): Card: ", parentgroup_card,
              ' Type: ', type(parentgroup_card))

        print("TRELLO: Got Card")
        if "**Subgroups:**" in parentgroup_card.description:
            parentgroup_card.set_description(
                parentgroup_card.description + "\n- {} -> {}".format(
                    newcard.name,
                    newcard.short_url
                )
            )
        else:
            parentgroup_card.set_description(
                parentgroup_card.description + "\n**Subgroups:**" + "\n- {} -> {}".format(
                    newcard.name,
                    newcard.short_url
                )
            )
        print("TRELLO: Added connection in Parent Card")

    card_url = newcard.short_url
    card_id = card_url.replace('https://trello.com/c/', '')

    return [card_id, card_url]


def delete_group(card_id, parentcard_id="", childrencards_id=[], siblings=[]):
    print("TRELLO: Delete Group Card")
    card = get_card(card_id)
    # DELETE REFERENCE IN PARENT CARD
    try:
        if parentcard_id not in ('', None):
            print("TRELLOC: delete_group(): Replacing Parent Description")
            parent = get_card(parentcard_id)
            description = re.sub(
                "- {} -> {}".format(card.name, card.short_url), '', parent.description)
            print('TRELLOC: Siblings: ', siblings)
            if siblings == []:
                description = description.replace('**Subgroups:**', '')
                description = description.rstrip()
            update_card(parentcard_id, desc=description)

        # DELETE CARD
        card.delete()
        print('TRELLOC: delete_group: Deleted Card')
    except:
        print("TRELLOC: Error in Deleting Group Card")

    # DELETE REFERENCE IN CHILDREN CARDS
    for children_id in childrencards_id:
        child = get_card(children_id)
        print('TRELLOC: delete_group(): Editing Child Description')
        description = child.description
        string = "\\*+Parent Group:\\*+ https://trello.com/c/{}".format(
            str(card_id))
        description = re.sub(string, '', description)
        description = description.rstrip()
        update_card(children_id, desc=description)


def add_call(call):
    print("TRELLO: --- ADD CALL ---")
    # GET INFORMATION TO PASS ON
    # add try: exept: statement
    parent_card = get_card(
        database.get_group_card(
            database.get(
                call.chat_id
            )[0].id
        )
    )

    labels = [client.get_label(upcoming_id, board_id)]
    description = ""

    # CREATE TRELLO CARD
    newcard = planned_calls_list.add_card(
        name=call.title, desc=description, labels=labels, position='top')
    print("TRELLO: Saved Call Card: ", newcard)

    # CREATE ATTACHMENTS
    parent_card.attach(name="Call", url=newcard.short_url)
    newcard.attach(name="Parent Group", url=parent_card.short_url)

    # RETURN VALUES
    card_url = newcard.short_url
    card_id = card_url.replace('https://trello.com/c/', '')
    return [card_id, card_url]


def delete_call(short_url):
    print("TRELLO: --- DELETE CALL ---")
    try:
        card = get_card(short_url)
        card.delete()
    except:
        print(
            'TRELLOC: delete_call(): failed in deleting call from Trello Board ', short_url)


def get_card(short_url):
    cards = board.all_cards()
    for card in cards:
        card_short_url = card.short_url
        if card_short_url.replace('https://trello.com/c/', '') == short_url:
            print("TRELLO - GET CARDS: Found matching card")
            return card
    return -1


def update_card(card_id, desc='', name='', due='', dueComplete=''):

    url = 'https://api.trello.com/1/cards/{}?'.format(card_id)

    if desc != '':
        desc.replace(' ', '%20')
        url += '&desc={}'.format(desc)

    if name != '':
        name.replace(' ', '%20')
        url += '&name={}'.format(name)

    if due != '':
        url += '&due={}'.format(due)

    if dueComplete != '':
        url += '&dueComplete={}'.format(dueComplete.upper())

    url += '&key={}&token={}'.format(TRELLO_KEY, TRELLO_TOKEN)
    headers = {"Accept": "application/json"}
    response = requests.request("PUT", url, headers=headers)
    print(json.dumps(json.loads(response.text),
                     sort_keys=True, indent=4, separators=(",", ": ")))


def clear_data():
    """
    This method will clear all cards in the trello board. It can be used when testing the program, to easily reset the data when something is broken.
    The data will still remain in the database and the board can be repopulated.
    """
    # calls list
    planned_calls_list.archive_all_cards()
    # dg list
    dg_list.archive_all_cards()
    # wg list
    wg_list.archive_all_cards()
    # project list
    projects_list.archive_all_cards()
    # past calls list
    past_calls_list.archive_all_cards()
    # archive list
    archive_list.archive_all_cards()
    print('TRELLOC: Archived all cards')
