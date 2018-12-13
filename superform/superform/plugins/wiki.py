import json
import sys

import requests

from superform import db, Post
from superform.utils import StatusCode

FIELDS_UNAVAILABLE = ["image"]
CONFIG_FIELDS = ["username", "password", "base_url"]


def run(publishing, channel_config):
    json_data = json.loads(channel_config)
    username = json_data['username']
    password = json_data['password']
    base_url = json_data['base_url']
    formatted_title = format_title(publishing.title)
    url = base_url + '/News/' + formatted_title + '-' + str(publishing.post_id) + '-' + str(publishing.channel_id)
    formatted_text = format_text(publishing.title, publishing.description)
    user = db.session.query(Post).filter(Post.id == publishing.post_id).filter(Post.user_id)
    try:
        response = requests.post(url, data={'n': 'News.' + formatted_title + '-' + str(publishing.post_id) + '-' + str(publishing.channel_id), 'text': formatted_text, 'action': 'edit',
                                            'post': '1', 'author': user, 'authid': username, 'authpw': password})
    except requests.exceptions.ConnectionError:
        return StatusCode.ERROR, "Couldn't connect to server", None
    except requests.exceptions.MissingSchema:
        return StatusCode.ERROR, "Wrong base_url, please check the format again", None

    if response.status_code != 200:
        return StatusCode.ERROR, 'Bad username or password', None

    # Fetch the page and check that it exists
    response = requests.get(url)
    if response.status_code != 200:
        return StatusCode.ERROR, 'News not published', None

    return StatusCode.OK, None, None


def format_text(title, description):
    """
    format the title and description to the pmwiki format
    :param title: title of the publishing
    :param description: description of the publishing
    :return: return the formatted title and description
    """
    return '(:title ' + title + ':)' + description


def format_title(title):
    """
    Format the title to fit the url
    :param title: title
    :return: formatted title
    """
    import re
    delimiters = "-", " ", ",", ";", ".", "\\", "/", "<", ">", "@", "?", "=", "+", "%", "*", "`", "\"", "\n", "&", "#", "_"
    pattern = '|'.join(map(re.escape, delimiters))
    split = re.split(pattern, title)
    formatted_title = ""
    for m in split:
        formatted_title += m

    return formatted_title
