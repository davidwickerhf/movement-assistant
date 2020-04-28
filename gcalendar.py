from __future__ import print_function
import datetime
import pickle
import os
import json
from datetime import datetime, timedelta
import utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


SCOPES = ['https://www.googleapis.com/auth/calendar']

# Pull API keys from Config Vars on Heroku or JSON file if local
# This pulls your variable out of Config Var and makes it available
client_secret = os.environ.get('GCALENDAR_SECRET')
if client_secret == None:  # This is to detect if you're working locally and the Config Var therefore isn't available
    client_secret = 'credentials.json'
else:
    # This converts the Config Var to JSON for OAuth
    with open('credentials.txt', 'w') as outfile:
        json.dump(client_secret, outfile)
        client_secret = 'credentials.txt'


if not (os.path.isfile('token.pkl') and os.path.getsize('token.pkl')) > 0:
    flow = InstalledAppFlow.from_client_secrets_file(
        client_secrets_file=client_secret, scopes=SCOPES)
    credentials = flow.run_console()
    pickle.dump(credentials, open("token.pkl", "wb"))

credentials = pickle.load(open("token.pkl", "rb"))
service = build('calendar', 'v3', credentials=credentials)


def add_event(date, time, duration, title, description, group, color):
    print("Time type: ", type(time))
    print("Date type: ", type(date))

    start_time_string = str(utils.str2date(date)) + \
        " " + str(utils.str2time(time))
    start_time = datetime.strptime(start_time_string, "%Y/%m/%d %H:%M:%S")
    print("Start time string: ", start_time_string)
    print(type(start_time))
    print("Start time: " + str(start_time))
    # Get end time calculating with the duration
    print("Duration string: ", duration)
    duration = timedelta(seconds=int(duration))
    print("Duration: " + str(duration))
    print("type: ", type(duration))

    end_time = start_time + duration
    print("End time: " + str(end_time))
    print(type(end_time))

    GMT_OFF = '+00:00'
    event = {
        'summary': title,
        'location': group,
        'start': {
            'dateTime': start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': GMT_OFF,
        },
        'end': {
            'dateTime': end_time.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': GMT_OFF,
        },
        'description': description,
        'colorId': str(color),
    }

    saved_event = service.events().insert(calendarId='primary', body=event,
                                          sendNotifications=True).execute()
    url = saved_event.get('htmlLink')
    event_id = saved_event['id']
    return [event_id, url]


def delete_event(event_id):
    print("CALENDAR: Delete Event: Id: ", event_id)
    service.events().delete(calendarId='primary', eventId=event_id).execute()
