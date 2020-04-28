from trello import TrelloClient
import os

TRELLO_KEY = os.environ.get('TRELLO_KEY')
TRELLO_TOKEN = os.environ.get('TRELLO_TOKEN')
TRELLO_SECRET = os.environ.get('TRELLO_SECRET')

client = TrelloClient(
    api_key=TRELLO_KEY,
    api_secret=TRELLO_SECRET,
    token=TRELLO_TOKEN,
)

board_id = "5e74996a963b6a6063936eed"
# LISTs IDs
board = client.get_board(board_id=board_id)
newgroup_list_id = "5e7499aa34052a6172bd0e3f"
planned_calls_list_id = "5e774f119849c8249f8f6541"
dg_list_id = "5e74999f6801d386764d77f4"
wg_list_id = "5e7499a2d7a1712de4fe2a84"
projects_list_id = "5e749a07819e72462465bac2"
past_calls_id = "5e98ee7ccafe1b1cd8061e76"
inactive_list_id = "5e749a11b808322c392daf7d"
archive_list_id = "5e749a16b2e2b0449d2f86f9"

# LISTS (COLUMNS) IN TRELLO BOARD
newgroup_list = client.get_list(newgroup_list_id)
planned_calls_list = client.get_list(planned_calls_list_id)
dg_list = client.get_list(dg_list_id)
wg_list = client.get_list(wg_list_id)
projects_list = client.get_list(projects_list_id)
past_calls_list = client.get_list(past_calls_id)
inactive_list = client.get_list(inactive_list_id)
archive_list = client.get_list(archive_list_id)

# LABELS IDs -  accessed by bots
upcoming_id = "5e74996a7669b225496b9f36"
active_id = "5e74996a7669b225496b9f35"
inactive_id = "5e74c0d2d9910d09dbd69398"
info_id = "5e74c1241056462f867de53a"
past_call_label_id = "5e7b985c53caf880abd11717"
# Restriction ids
restrictions = {'Open': "5e74c103eb262b15b2783cb1",
                "Restricted": "5e74c0f5daeb322dd3f54f03",
                "Closed": "5e74996a7669b225496b9f39"}
# Region ids
regions = {"Global": "5e7740041c091925059656c0",
           "Europe": "5e773fa24961ce27cdd18cd0",
           "South America": "5e773fac463f9a7c1c4de2a6",
           "North America": "5e773fdaa97caa255bcfbb5e",
           "Africa": "5e773fc8c4832c7cd2832227",
           "Asia": "5e773fac463f9a7c1c4de2a6",
           "Oceania": "5e773fe4ea817135d4f3cbb8"}

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
    else:
        group_list = newgroup_list
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
