import facebook
import json

from superform.utils import login_required
from flask import Blueprint, url_for, app

FIELDS_UNAVAILABLE = ['Title']

CONFIG_FIELDS = ["access_token","page"]


def get_url_for_token(id_channel):
    app_id = "1672680826169132"
    canvas_url = "https://127.0.0.1:5000/callback_fb"
    perms = ["manage_pages", "publish_pages"]
    graph = facebook.GraphAPI()
    url = graph.get_auth_url(app_id, canvas_url, perms)
    return url + "&state=" + str(id_channel)


def run(publishing,channel_config):
    json_data = json.loads(channel_config)
    acc_tok = json_data['access_token']
    page = json_data['page']
    graph = facebook.GraphAPI(access_token=acc_tok)
    graph.put_object(
        parent_object="me",
        connection_name=page,
        message="This is a great website. Everyone should visit it.",
        link="link=publishing.link_url")

def get_page(channel_config):
    json_data = json.loads(channel_config)
    acc_tok = json_data['access_token']
    graph = facebook.GraphAPI(access_token=acc_tok)
    pages = graph.get_connections(id='me', connection_name='pages')
    return pages