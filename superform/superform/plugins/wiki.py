import json
import sys

import requests

from superform import db, Post

FIELDS_UNAVAILABLE = ["date_from", "date_until", "image"]
CONFIG_FIELDS = ["username", "password", "base_url"]


def run(publishing, channel_config):
    json_data = json.loads(channel_config)
    username = json_data['username']
    password = json_data['password']
    base_url = json_data['base_url']
    url = base_url + '/News/' + format_title(publishing.title)
    formatted_title = format_title(publishing.title)
    formatted_text = format_text(publishing.title, publishing.description)
    user = db.session.query(Post).filter(Post.id == publishing.post_id).filter(Post.user_id)
    response = requests.post(url, data={'n': 'News.' + formatted_title, 'text': formatted_text, 'action': 'edit',
                                             'post': '1', 'author': user, 'authid': username, 'authpw': password})

    if response.status_code != 200:
        print(response.reason, file=sys.stderr)


def format_text(title, description):
    return '(:title ' + title + ':)' + description


def format_title(title):
    import re
    delimiters = " ", ",", ";", ".", "\\", "/", "<", ">", "@", "?", "=", "+", "%", "*", "`", "\"", "\n", "&", "#", "_"
    pattern = '|'.join(map(re.escape, delimiters))
    split = re.split(pattern, title)
    formatted_title = ""
    for m in split:
        formatted_title += m

    return formatted_title