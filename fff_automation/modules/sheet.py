import os
import json
import pickle
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from fff_automation.modules import settings

if not (os.path.isfile('fff_automation/secrets/sheet_token.pkl') and os.path.getsize('fff_automation/secrets/sheet_token.pkl') > 0):
    # use creds to create a client to interact with the Google Drive API
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive']
    # CREDENTIALS HAVE NOT BEEN INITIALIZED BEFORE
    client_secret = os.environ.get('CLIENT_SECRET')
    if client_secret == None:
        # CODE RUNNING LOCALLY
        print('DATABASE: Resorted to local JSON file')
        with open('fff_automation/secrets/client_secret.json') as json_file:
            client_secret_dict = json.load(json_file)
    else:
        # CODE RUNNING ON SERVER
        client_secret_dict = json.loads(client_secret)
        print("JSON CLIENT SECRET:  ", type(client_secret_dict))

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        client_secret_dict, scope)
    pickle.dump(creds, open(
        'fff_automation/secrets/sheet_token.pkl', 'wb'))

creds = pickle.load(
    open("fff_automation/secrets/sheet_token.pkl", "rb"))
client = gspread.authorize(creds)

# IF NO SPREADSHEET ENV VARIABLE HAS BEEN SET, SET UP NEW SPREADSHEET
if settings.get_var('SPREADSHEET') == -1:
    print("DATABASE: Create new database")
    settings.set_sheet(client)
print("DATABASE: id == ", settings.get_var('SPREADSHEET'))

SPREADSHEET = settings.get_var('SPREADSHEET')
spreadsheet = client.open_by_key(SPREADSHEET)
groupchats = spreadsheet.get_worksheet(0)
archive = spreadsheet.get_worksheet(1)
logs = spreadsheet.get_worksheet(2)


def log(timestamp, user_id, action, group_name):
    print('LOG')
    logs.append_row([timestamp, user_id, action, group_name])
