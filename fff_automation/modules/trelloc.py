import os
import emoji
from trello import TrelloClient
from fff_automation.modules import settings


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
                labels_dict[num+7] = label.id
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


def add_group(title, admins, purpose="", onboarding="",  platform="", region="", group_type="", restriction="", is_subgroup="", parentgroup_id="", date=""):
    # SET LABELS
    labels = []
    if region != "":
        labels.append(client.get_label(regions[region], board_id))
    if restriction != "":
        labels.append(client.get_label(restrictions[restriction], board_id))
    print("TRELLO: Got labels: ", labels)

    group_list = ""
    # SELECT LIST
    if group_type == WORKING_GROUP:
        group_list = wg_list
    elif group_type == DISCUSSION_GROUP:
        group_list = dg_list
    elif group_type == PROJECT:
        group_list == projects_list
    print("TRELLO: Got list")

    # SET DESCRIPTION
    description = "**INTERNATIONAL {}**\n **Purpose: **{}\n\n**Onboarding:** {}\n\n**Group Category:** {}\n**Group Region:** {}\n**Group Platform:** {}\n**Group Admins:** {}\n\n**Registered on:** {}".format(
        group_type.upper(), purpose, onboarding, group_type, region, platform, admins, date)

    # ATTACH PARENT CARD LINK TO DESCRIPTION
    if parentgroup_id != "":
        description = description + \
            "\n\n**Parent Group:** https://trello.com/c/{}".format(
                str(parentgroup_id))
    print("TRELLO: Set description")

    # SAVE CARD AND GET ID
    newcard = group_list.add_card(
        name=title, desc=description, labels=labels, position="bottom")
    print("TRELLO: Saved Card: ", newcard)
    print("TRELLO: Card type: ", type(newcard))

    # ATTACH CARD TO PARENT DESCRIPTION
    if parentgroup_id != '':
        parentgroup_card = get_card(parentgroup_id)
        print("TRELLO: Got Card")
        if "**Subgroups:**" in parentgroup_card.description:
            parentgroup_card.set_description(parentgroup_card.description +
                                             "\n- {} -> {}".format(newcard.name, newcard.short_url))
        else:
            parentgroup_card.set_description(parentgroup_card.description + "\n**Subgroups:**"
                                             "\n- {} -> {}".format(newcard.name, newcard.short_url))
        print("TRELLO: Added connection in Parent Card")

    card_url = newcard.short_url
    card_id = card_url.replace('https://trello.com/c/', '')

    return [card_id, card_url]


def delete_group(card_id, parentcard_id="", childrencards_id=[]):
    print("TRELLO: Delete Group Card")
    card = get_card(card_id)
    # DELETE REFERENCE IN PARENT CARD
    if parentcard_id != "":
        parent = get_card(parentcard_id)
        description = parent.description.replace(
            "\n- {} -> {}".format(card.name, card.short_url), '')
        parent.set_description(description)
    # DELETE REFERENCE IN CHILDREN CARDS
    if childrencards_id != []:
        for children_id in childrencards_id:
            child = get_card(children_id)
            description = parent.description.replace("\n\n**Parent Group:** https://trello.com/c/{}".format(
                str(card_id)), '')
            child.set_description(description)
    # DELETE CARD
    card.delete()


def add_call(title, groupchat, group_trello_id, date, time, duration, description, agenda_link, calendar_link, registred_by):
    print("TRELLO: --- ADD CALL ---")
    # GET INFORMATION TO PASS ON
    parent_card = get_card(group_trello_id)
    try:
        if parent_card == -1:
            print("TRELLO: Parent Card Not Found")
    except:
        print("TRELLO: Card was found with no error")
    labels = [client.get_label(upcoming_id, board_id)]
    description = ""

    # CREATE TRELLO CARD
    newcard = planned_calls_list.add_card(
        name=title, desc=description, labels=labels, position='top')
    print("TRELLO: Saved Call Card: ", newcard)

    # CREATE ATTACHMENTS
    parent_card.attach(name="Call", url=newcard.short_url)
    newcard.attach(name="Parent Group", url=parent_card.short_url)

    # RETURN VALUES
    card_url = newcard.short_url
    card_id = card_url.replace('https://trello.com/c/', '')
    return [card_id, card_url]


def get_card(short_url):
    cards = board.all_cards()
    for card in cards:
        card_short_url = card.short_url
        if card_short_url.replace('https://trello.com/c/', '') == short_url:
            print("TRELLO - GET CARDS: Found matching card")
            return card
    return -1
