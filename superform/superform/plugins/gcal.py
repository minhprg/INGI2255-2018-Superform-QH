from flask import make_response, redirect, url_for
import json
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
import os
from superform.utils import StatusCode

FIELDS_UNAVAILABLE = ['Image_url','Link_url']

CONFIG_FIELDS = ["calendar id", "clientID", "clientSecret"]

SCOPES = 'https://www.googleapis.com/auth/calendar'

flow = None
client_id = None
calendarId = None
start = {}
end = {}


def run(publishing,channel_config):
    global flow, client_id, calendarId
    json_data = json.loads(channel_config)

    calendarId = json_data['calendar id']
    client_id = json_data['clientID']
    client_secret = json_data['clientSecret']

    event = {}
    event['summary'] = publishing.title
    event['description'] = publishing.description

    start['dateTime'] = publishing.date_from.isoformat()

    end['dateTime'] = publishing.date_until.isoformat()

    flow = OAuth2WebServerFlow(client_id, client_secret, SCOPES, redirect_uri= 'http://127.0.0.1:5000/return_gcal')

    try:
        credentials = get_credentials()

        if not credentials or credentials.invalid:
            return StatusCode.URL, None, None, respond_redirect_to_auth_server()
        else:
            return insert_in_gcal(credentials,event)

    except Exception as e:
        print(e)
        return StatusCode.ERROR, str(e), None


def get_credentials():
    """Using the fake user name as a key, retrieve the credentials."""
    storage = Storage(os.path.dirname(__file__) + '\\gcal\\credentials-%s.dat' % client_id)
    return storage.get()


def save_credentials(credentials):
    """Using the fake user name as a key, save the credentials."""
    storage = Storage(os.path.dirname(__file__) + '\\gcal\\credentials-%s.dat' % client_id)
    storage.put(credentials)


def respond_redirect_to_auth_server():
    """Respond to the current request by redirecting to the auth server."""
    #
    # This is an important step.
    #
    # We use the flow object to get an authorization server URL that we should
    # redirect the browser to. We also supply the function with a redirect_uri.
    # When the auth server has finished requesting access, it redirects
    # back to this address. Here is pseudocode describing what the auth server
    # does:
    #   if (user has already granted access):
    #     Do not ask the user again.
    #     Redirect back to redirect_uri with an authorization code.
    #   else:
    #     Ask the user to grant your app access to the scope and service.
    #     if (the user accepts):
    #       Redirect back to redirect_uri with an authorization code.
    #     else:
    #       Redirect back to redirect_uri with an error code.
    uri = flow.step1_get_authorize_url()

    # Set the necessary headers to respond with the redirect. Also set a cookie
    # to store our fake_user name. We will need this when the auth server
    # redirects back to this server.
    response = make_response(redirect(location=uri, code=301))
    response.headers['Cache-Control'] = 'no-cache'
    return response


def insert_in_gcal(credentials, event):
    try:
        service = build('calendar', 'v3', http=credentials.authorize(Http()))
        # Call the Calendar API
        setting = service.settings().get(setting='timezone').execute()

        start['timeZone'] = setting['value']
        event['start'] = start

        end['timeZone'] = setting['value']
        event['end'] = end

        event = service.events().insert(calendarId=calendarId, body=event).execute()
        print('Event created: %s' % (event.get('htmlLink')))
        return StatusCode.OK, None, None

    except AccessTokenRefreshError:
        # This may happen when access tokens expire. Redirect the browser to
        # the authorization server
        return StatusCode.URL, None, None, respond_redirect_to_auth_server()


def confirm(code):
    credentials = flow.step2_exchange(code)

    # Call a helper function defined below to save these credentials.
    save_credentials(credentials)

    insert_in_gcal(credentials)

    return redirect(url_for('index'))
