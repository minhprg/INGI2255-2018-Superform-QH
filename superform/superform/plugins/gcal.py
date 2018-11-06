from flask import current_app
import json
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

FIELDS_UNAVAILABLE = ['Image_url']

CONFIG_FIELDS = ["creds"]

SCOPES = 'https://www.googleapis.com/auth/calendar'

def run(publishing,channel_config):
    json_data = json.loads(channel_config)

    creds = json_data['creds']

    event = {}
    event['summary'] = publishing.title
    event['description'] = publishing.description + "\nlink:\n" + publishing.link_url

    start = {}
    start['dateTime'] = publishing.date_from.isoformat()
    start['timeZone'] = 'America/Los_Angeles'
    event['start'] = start

    end = {}
    end['dateTime'] = publishing.date_until.isoformat()
    end['timeZone'] = 'America/Los_Angeles'
    event['end'] = end

    #event = json.loads(event)

    try:
        store = file.Storage('token.json')
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
            creds = tools.run_flow(flow, store)
        service = build('calendar', 'v3', http=creds.authorize(Http()))

        # Call the Calendar API

        event = service.events().insert(calendarId='primary', body=event).execute()
        print('Event created: %s' % (event.get('htmlLink')))
    except Exception as e:
        #TODO should add log here
        print(e)
