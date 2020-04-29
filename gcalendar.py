from __future__ import print_function
import datetime
import pickle
import os
import json
from datetime import datetime, timedelta
import utils
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from google.auth.transport.requests import Request

if not (os.path.isfile('calendar_token.pkl') and os.path.getsize('calendar_token.pkl') > 0):
    scope = ['https://www.googleapis.com/auth/calendar']
    # CREDENTIALS HAVE NOT BEEN INITIALIZED BEFORE
    client_secret = os.environ.get('CLIENT_SECRET')
    if client_secret != None:
        # CODE RUNNING ON SERVER
        client_secret_dict = json.loads(client_secret)
        print("JSON CLIENT SECRET:  ", type(client_secret_dict))
    else:
        # CODE RUNNING LOCALLY
        print("CALENDAR: Resorted to local JSON file")
        with open('client_secret.json') as json_file:
            client_secret_dict = json.load(json_file)

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        client_secret_dict, scopes=scope)
    pickle.dump(creds, open("calendar_token.pkl", "wb"))


credentials = pickle.load(open("calendar_token.pkl", "rb"))
service = build('calendar', 'v3', credentials=credentials)


def add_event(date, time, duration, title, description, group, color):
    print("CALENDAR: Time type: ", type(time))
    print("CALENDAR: Date type: ", type(date))

    start_time_string = str(utils.str2date(date)) + \
        " " + str(utils.str2time(time))
    start_time = datetime.strptime(start_time_string, "%Y/%m/%d %H:%M:%S")
    print("CALENDAR: Start time string: ", start_time_string)
    print(type(start_time))
    print("CALENDAR: Start time: " + str(start_time))
    # Get end time calculating with the duration
    print("CALENDAR: Duration string: ", duration)
    duration = timedelta(seconds=int(duration))
    print("CALENDAR: Duration: " + str(duration))
    print("CALENDAR: type: ", type(duration))

    end_time = start_time + duration
    print("CALENDAR: End time: " + str(end_time))
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

    calendar_id = os.environ.get(key='CALENDAR_ID', default='primary')
    saved_event = service.events().insert(calendarId=calendar_id, body=event,
                                          sendNotifications=True).execute()
    url = saved_event.get('htmlLink')
    event_id = saved_event['id']
    return [event_id, url]


def delete_event(event_id):
    calendar_id = os.environ.get(key='CALENDAR_ID', default='primary')
    print("CALENDAR: Delete Event: Id: ", event_id)
    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
