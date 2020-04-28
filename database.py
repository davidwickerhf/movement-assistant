import gspread
import os
import json
from oauth2client.service_account import ServiceAccountCredentials
import gcalendar
import trelloc
import utils

# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive',
         'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']

# Pull API keys from Config Vars on Heroku or JSON file if local
# This pulls your variable out of Config Var and makes it available
client_secret = os.environ.get('DATABASE_SECRET')
if client_secret == None:  # This is to detect if you're working locally and the Config Var therefore isn't available
    print('CALENDAR: Resorted to local JSON file')
    # ... so it pulls from the locally stored JSON file.
    with open('client_secret.json') as json_file:
        client_secret = json.load(json_file)
else:
    # This converts the Config Var to JSON for OAuth
    client_secret = json.load(client_secret)

creds = ServiceAccountCredentials.from_json_keyfile_dict(client_secret, scope)
client = gspread.authorize(creds)

# Find a workbook by name and open the first sheet
SPREADSHEET = os.environ['SPREADSHEET']
# -- DELETE WHEN DEPLOYING TO HEROKU
spreadsheet = client.open_by_key(SPREADSHEET)
groupchats = spreadsheet.get_worksheet(0)
archive = spreadsheet.get_worksheet(1)
deleted = spreadsheet.get_worksheet(2)


def save_group(chat_id, title, admins, category="", region="", platform="", restriction="", date="", is_subgroup=False, parentgroup="", purpose="", onboarding="", link=""):
    # try:
    # GET GROUP ADMINS
    admins_string = ""
    for chatMemeber in admins:
        print("DATABASE: Getting group admins")
        user = chatMemeber.user
        try:
            admins_string = admins_string + "@" + user.username + "; "
        except:
            admins_string = admins_string + user.first_name + " " + user.last_name + "; "
    admins_string = admins_string[:-2]
    print("DATABASE: Got Admins")

    # GET RANDOM CALENDAR COLOR:
    color_id = utils.get_random_event_color()
    print("DATABASE: Got Group Color")

    # CREATE TRELLO CARD
    if parentgroup != '':
        parent_card = get_group_card(parentgroup)
        print("DATABASE: Got parent card")
    else:
        parent_card = ""
        print("DATABASE: No parent")
    card_info = trelloc.add_group(title, admins_string, purpose, onboarding,
                                  platform, region, category, restriction, is_subgroup, parent_card, date)
    card_id = card_info[0]
    card_url = card_info[1]
    print("DATABASE: Got Trello Card Info")

    # CREATE NEW WORKSHEET
    try:
        calls_sheet = spreadsheet.worksheet(str(chat_id))
    except:
        print("DATABASE: Creating New Sheet for new group")
        calls_sheet = spreadsheet.add_worksheet(
            title=str(chat_id), rows="1000", cols="1")
        calls_sheet.append_row(["EVENT ID", "CHAT ID", "CARD ID", "GROUP", "TITLE", "DATE", "TIME", "DURATION",
                                "DESCRIPTION", "AGENDA LINK", "CALENDAR LINK", "CARD LINK", "USER ID"])

    # SAVE GROUP IN DATABASE
    print("DATABASE: Saved group")
    groupchats.append_row([chat_id, card_id, title, category, region, admins_string,
                           platform, color_id, restriction, is_subgroup, parentgroup, purpose, onboarding, card_url, link])

    # SAVE IN KUMA BOARD

    return card_url


def update_group(chat_id, title, admins, category="", level="",
                 platform="", purpose="", mandate="", onboarding="", link=""):
    try:
        row = find_row_by_id(chat_id)[0]
    except:
        save_group(chat_id, title, category, level,
                   admins, platform, purpose, mandate, onboarding, link)
    # function is not complete


def archive_group(chat_id, username):
    print("DATABASE: Archive Group Started")
    group_info = find_row_by_id(chat_id)[0]
    group_info.append(str(utils.now_time()))
    # ADD GROUP INFO TO ARCHIVE
    archive.append_row(group_info)
    # function is not complete


def delete_group(chat_id, username):
    print("DATABASE: Delete Group Started")
    row = find_row_by_id(item_id=chat_id)[0]
    print("DATABASE: Got row number")
    group_info = groupchats.row_values(row)
    print("DATABASE: Got Row info")
    try:
        calls = spreadsheet.worksheet(str(chat_id))
        print("DATABASE: Got calls worksheet")

        # DELETE CALENDAR EVENTS
        events_info = calls.get_all_values()
        events_info.pop(0)
        print("DATABASE: Event Info: ", events_info)
        for event in events_info:
            print("DATABASE: Event", event)
            gcalendar.delete_event(event[0])

        # ARCHIVE TRELLO CALL CARDS
        # try:
        #    call_card_id = get_group_card(chat_id)
        #    trelloc.delete_group(call_card_id)
        #    print("DATABASE: Deleted Trello card")
        # except:
        #    print("DATABASE: No Trello Card found")

        # DELETE LINKED CALL SHEET
        spreadsheet.del_worksheet(calls)

    except:
        print("DATABASE: No Calls sheet found")

    # DELETE CARD IN TRELLO
    try:
        card_id = get_group_card(chat_id)
        trelloc.delete_group(card_id)
        print("DATABASE: Deleted Trello card")
    except:
        print("DATABASE: No Trello Card found")

    # DELETE CHILDREN LINKS IN DATABASE
    children = find_row_by_id(item_id=chat_id, col=11)
    print("DATABASE:  Children: ", children, " Type: ", type(children))
    if children[0] != -1:
        for child in children:
            groupchats.update_cell(child, 11, '')
    print("DATABASE:  Deleted children")

    # DROP UNNECESSAY INFO
    unwanted = [0, 1, 9, 12, 13]
    for ele in sorted(unwanted, reverse=True):
        del group_info[ele]
    group_info.extend((utils.now_time().strftime("%Y/%m/%d %H:%M"), username))
    print("DATABASE: Dropped info")

    # SAVE INFO IN DELETE SHEET
    deleted.append_row(group_info)

    # REMOVE ROW FROM GROUPS DATABASE
    groupchats.delete_row(find_row_by_id(item_id=chat_id)[0])


def save_call(message_id, chat_id, title, date, time, user_id, duration, description="", agenda_link="", username=""):
    # GET CALLS WORKSHEET
    try:
        calls = spreadsheet.worksheet(str(chat_id))
    except:
        print("Chat is not registerred")
        return -1

    # SAVE TO CALENDAR
    group_title = get_group_title(chat_id)
    group_color = get_group_color(chat_id)
    values = gcalendar.add_event(
        date, time, duration, title, description, group_title, group_color)
    print("Added call to calendar")
    event_id = values[0]
    calendar_url = values[1]

    # DURATION STRING TO INT
    seconds = int(duration)
    hours = seconds / 3600
    rest = seconds % 3600
    minutes = rest / 60
    duration_string = str(hours) + " Hours, " + str(minutes) + " Minutes"

    # SAVE IN TRELLO
    values = trelloc.add_call(title, get_group_title(group_id=chat_id), get_group_card(
        group_id=chat_id), date, time, duration, description, agenda_link, calendar_url, username)
    trello_url = values[1]
    card_id = values[0]

    # SAVE EVENT IN DATABASE
    calls.append_row([event_id, chat_id, card_id, group_title, title, date, time,
                      duration_string, description, agenda_link, calendar_url, trello_url, user_id])
    print("Saved call in database")
    return [calendar_url, trello_url]


def find_row_by_id(sheet=groupchats, item_id="", col=1):
    if(sheet == "groups"):
        sheet = groupchats
    elif(sheet == "calls"):
        sheet = spreadsheet.worksheet(str(item_id))
        col = 2

    column = sheet.col_values(col)
    rows = []
    for num, cell in enumerate(column):
        print("DATABASE FIND ID: ", cell, " | ", item_id)
        if str(cell) == str(item_id):
            rows.append(num+1)
            print("DATABASE: Found group at row ", num+1)
            # need to remove child parent info now
    if rows == []:
        print("DATABASE FIND ID: No Matching field found")
        rows.append(-1)
    return rows


def get_group_title(group_id, sheet=groupchats):
    print("DATABASE: get_group_title()")
    row = find_row_by_id(sheet, group_id)[0]
    group_title = sheet.cell(row, 3).value
    return group_title


def get_group_color(group_id, sheet=groupchats):
    print("DATABASE: get_group_color()")
    row = find_row_by_id(sheet, group_id)[0]
    group_color = sheet.cell(row, 8).value
    return group_color


def get_group_card(group_id, sheet=groupchats):
    print("DATABASE: get_group_card()")
    row = find_row_by_id(sheet, group_id)[0]
    if row == -1:
        return row
    card_id = sheet.cell(row, 2).value
    return card_id


def get_call_card(group_id, index=0):
    sheet = spreadsheet.worksheet(str(group_id))
    row = find_row_by_id(sheet, group_id)[index]
    if row[0] == -1:
        return row
    card_id = sheet.cell(row, 3).value
    return card_id


def get_all_groups(sheet=groupchats):
    groups = sheet.get_all_values()
    groups.pop(0)
    return groups


def rotate_groups(first_index, direction, size=5):
    groups = get_all_groups(groupchats)
    if direction == 0:
        final_index = first_index - size
        if final_index >= 0:
            rotated_groups = groups[final_index:first_index]
        else:
            rotated_groups = groups[final_index:0]
            final_index = 0
    elif direction == 1:
        final_index = first_index + size
        if final_index <= len(groups):
            rotated_groups = groups[first_index-1:final_index]
        else:
            rotated_groups = groups[first_index-1:len(groups)-1]
            final_index = len(groups)-1
    print("DATABASE: Check Test")
    print("DATABASE - Rotate Groups: ", rotated_groups,
          " | Final Index: ", final_index)
    return [rotated_groups, final_index]
