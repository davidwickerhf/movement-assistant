import os
from trello import TrelloClient
import gspread
import requests
import json


def set_envs():
    """
    Set enviroment variables if code is run locally:
    TOKEN, SPREADSHEET (token), TRELLO_KEY, TRELLO_SECRET, TRELLO_TOKEN, CALENDAR_ID
    Replace the tokens/keys in this scripts with the ones you have access to.
    """
    with open('fff_automation/secrets/env_variables.json') as json_file:
        vars_dict = json.load(json_file)

    # TRELLO SECRETS
    os.environ['TRELLO_KEY'] = vars_dict.get('TRELLO_KEY')
    print("- - >SET ENV VARS: Trello Key: ", vars_dict.get('TRELLO_KEY'))
    os.environ['TRELLO_TOKEN'] = vars_dict.get('TRELLO_TOKEN')
    # TELEGRAM BOT TOKEN
    os.environ['TOKEN'] = vars_dict.get('BOT_TOKEN')
    # USER VARIABLES
    os.environ['CALENDAR_ID'] = vars_dict.get('CALENDAR_ID')
    os.environ['GDRIVE_EMAIL'] = vars_dict.get('GDRIVE_EMAIL')
    # SPREADSHEET ID - This field should be left empty ( "" or None ) in which case, a new spreadsheet will be created automatically in the correct format.
    os.environ['SPREADSHEET'] = vars_dict.get('SPREADSHEET')
    # TRELLO BOARD ID - This field should be left empty ( "" or None ) in which case, a new board will be created automatically in the correct format.
    os.environ['TRELLO_BOARD_ID'] = vars_dict.get('TRELLO_BOARD_ID')


def set_trello(client, key, token):
    """
    Setup Trello Board if none exists yet.
    This will save the new board/list/labels ids as enviroment variables
    :client: Trello Client, generated through credentials in the trelloc.py module
    :key: Key of the Trello Client used by the user
    :token: Token of the Trello Client initiated by the user
    """
    # CREATE BOARD
    url = "https://api.trello.com/1/boards/"
    querystring = {"name": "Transparency Board", "key": key, "token": token}
    response = requests.request("POST", url, params=querystring)
    board_id = response.json()["shortUrl"].split("/")[-1].strip()
    os.environ['TRELLO_BOARD_ID'] = board_id
    board = client.get_board(board_id=board_id)
    lists = board.get_lists()
    for trello_list in lists:
        trello_list.close()


    # CREATE LISTS
    # Board info list
    os.environ['TRELLO_INFO_LIST'] = board.add_list(
        name="INFORMATION", pos="bottom").id
    # Calls list
    os.environ['TRELLO_CALLS_LIST'] = board.add_list(
        name="INFORMATION", pos="bottom").id
    # discussion groups
    os.environ['TRELLO_DG_LIST'] = board.add_list(
        name="INFORMATION", pos="bottom").id
    # working groups
    os.environ['TRELLO_WG_LIST'] = board.add_list(
        name="INFORMATION", pos="bottom").id
    # projects groups
    os.environ['TRELLO_PROJECTS_LIST'] = board.add_list(
        name="INFORMATION", pos="bottom").id
    # past calls
    os.environ['TRELLO_PAST_CALLS_LIST'] = board.add_list(
        name="INFORMATION", pos="bottom").id
    # archive
    os.environ['TRELLO_ARCHIVE_LIST'] = board.add_list(
        name="INFORMATION", pos="bottom").id

    # CREATE LABELS
    os.environ['TRELLO_UPCOMING_LABEL'] = board.add_label(
        name="UPCOMING", color="yellow").id
    os.environ['TRELLO_CLOSEDGROUP_LABEL'] = board.add_label(
        name="CLOSED GROUP", color="purple").id
    os.environ['TRELLO_RESTRICTEDGROUP_LABEL'] = board.add_label(
        name="RESTRICTED GROUP", color="blue").id
    os.environ['TRELLO_OPENGROUP_LABEL'] = board.add_label(
        name="OPEN GROUP", color="sky").id
    os.environ['TRELLO_AFRICA_LABEL'] = board.add_label(
        name="AFRICA", color="black").id
    os.environ['TRELLO_ASIA_LABEL'] = board.add_label(
        name="ASIA", color="black").id
    os.environ['TRELLO_EUROPE_LABEL'] = board.add_label(
        name="EUROPE", color="black").id
    os.environ['TRELLO_NORTHAMREICA_LABEL'] = board.add_label(
        name="NORTH AMERICA", color="black").id
    os.environ['TRELLO_SOUTHAMERICA_LABEL'] = board.add_label(
        name="SOUTH AMERICA", color="black").id
    os.environ['TRELLO_OCEANIA_LABEL'] = board.add_label(
        name="OCEANIA", color="black").id
    os.environ['TRELLO_GLOBAL_LABEL'] = board.add_label(
        name="GLOBAL", color="black").id
    os.environ['TRELLO_PASTCALL_LABEL'] = board.add_label(
        name="PAST CALL", color="black").id

    # CREATE INFO CARD
    client.get_list(os.environ.get('TRELLO_INFO_LIST')).add_card(name="IMPORTANT INFORMATION",
                                                                 desc="You can edit the cards in the \"INFORMATION\" list as you wish, but don't edit the cards nor the list order of the other lists as it might break the way the code works.")


def set_database(client):
    """
    Setup spreadsheet database if none exists yet.
    The service email you created throught the Google API will create the new spreadsheet and share it with the email you indicated in the GDRIVE_EMAIL enviroment variable. You will find the spreadsheet database in your google drive shared folder.
    Don't change the order of the worksheets or it will break the code.
    :credentials: Credentials created in database.py
    """
    # CREATE SPREADSHEET
    spreadsheet = client.create('DATABASE')
    os.environ['SPREADSHEET'] = spreadsheet.id

    # CREATE GROUP CHATS SHEET
    groupchats = spreadsheet.add_worksheet(
        title="Groupchats", rows="150", cols="15")
    groupchats.append_row(["GROUP ID", "CARD ID", "TITLE", "CATEGORY", "REGION", "ADMINS", "PLATFORM",
                           "COLOR", "RESTRICTION", "IS SUBGROUP", "PARENT GROUP", "PURPOSE", "ONBOARDING"])

    # CREATE ARCHIVE SHEET
    archive = spreadsheet.add_worksheet(title="Archive", rows="150", cols="13")
    archive.append_row(["GROUP ID", "CARD ID", "TITLE", "CATEGORY", "REGION", "ADMINS",
                        "PLATFORM", "COLOR", "PURPOSE", "ONBOARDING", "TRELLO LINK", "DATE OF ARCHIVAL"])

    # CREATE DELETED SHEET
    deleted = spreadsheet.add_worksheet(title="Deleted", rows="150", cols="11")
    deleted.append_row(["TITLE", "CATEGORY", "REGION", "ADMINS", "PLATFORM", "COLOR",
                        "RESTRICTION", "PURPOSE", "ONBOARDING", "DATE OF DELETION", "DELETED BY"])

    # SHARE SPREADSHEET
    spreadsheet.share(value=os.environ.get('GDRIVE_EMAIL'),
                      perm_type="user", role="owner")
