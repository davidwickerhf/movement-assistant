from trello import TrelloClient
import os
from setup import set_env

TRELLO_KEY = os.environ.get('TRELLO_KEY')
TRELLO_TOKEN = os.environ.get('TRELLO_TOKEN')

if TRELLO_KEY == "" or None or "insert_here" or TRELLO_TOKEN == "" or None or "insert_here":
    print("TRELLOC: AUTH ERROR: Trello Keys missing: ", TRELLO_KEY)


client = TrelloClient(
    api_key=TRELLO_KEY,
    token=TRELLO_TOKEN,
)

if os.environ.get('TRELLO_BOARD_ID') == "" or None:
    set_env.set_trello(client)
board_id = os.environ.get('TRELLO_BOARD_ID')


# LISTs IDs
board = client.get_board(board_id=board_id)
lists = board.all_lists()

# LISTS (COLUMNS) IN TRELLO BOARD
planned_calls_list = lists[1]
dg_list = lists[2]
wg_list = lists[3]
projects_list = lists[4]
past_calls_list = lists[5]
archive_list = lists[6]

# LABELS IDs -  accessed by bots
labels_ids = board.get_labels()
upcoming_id = labels_ids[0].id
past_call_label_id = labels_ids[11].id
# Restriction labels ids
restrictions = {'Open': labels_ids[4].id,
                "Restricted": labels_ids[3].id,
                "Closed": labels_ids[2].id}
# Region labels ids
regions = {"Global": labels_ids[8].id,
           "Europe": labels_ids[7].id,
           "South America": labels_ids[12].id,
           "North America": labels_ids[9].id,
           "Africa": labels_ids[5].id,
           "Asia": labels_ids[6].id,
           "Oceania": labels_ids[10].id}

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
        name=title, desc=description, labels=labels, position="bottom")
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
