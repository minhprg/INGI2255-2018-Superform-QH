import os
import tempfile

import pytest

from superform.models import Authorization, Channel
from superform import app, db, Post, User, Publishing
from superform.utils import datetime_converter, str_converter, get_module_full_name
from superform.users import  is_moderator, get_moderate_channels_for_user,channels_available_for_user
from superform.plugins import linkedin


@pytest.fixture
def client():
    app.app_context().push()
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    client = app.test_client()

    with app.app_context():
        db.create_all()

    yield client

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])


def login(client, login):
    with client as c:
        with c.session_transaction() as sess:
            if login is not "myself":
                sess["admin"] = True
            else:
                sess["admin"] = False

            sess["logged_in"] = True
            sess["first_name"] = "gen_login"
            sess["name"] = "myname_gen"
            sess["email"] = "hello@genemail.com"
            sess['user_id'] = login


def create_channel(client, name, module):
    data1 = {'@action': 'new', 'name': name, 'module': module}
    rv = client.post('/channels', data=data1, follow_redirects=True)
    assert rv.status_code == 200
    assert name in rv.data.decode()


def get_channel(client, name):
    for i in range(1000):
        channel = Channel.query.get(i)
        if channel != None and channel.name == name:
            return channel


def delete_channel(client, id, name):
    data = {'@action': 'delete'}
    data['id'] = id
    rv = client.post('/channels', data=data, follow_redirects=True)
    assert rv.status_code == 200


def test_valid_module(client):
    try:
        from superform.plugins.linkedin import run
    except ImportError:
        assert False

    assert 'FIELDS_UNAVAILABLE' in dir(linkedin)
    assert 'CONFIG_FIELDS' in dir(linkedin)


def test_valid_linkedin_configuration(client):
    assert "LINKEDIN_API_KEY" in client.application.config
    assert "LINKEDIN_API_SECRET" in client.application.config


def test_callback_no_param(client):
    """ No parameters given on callback -> redirected to channels """
    login(client, "admin")
    rv = client.get('/callback_In', follow_redirects=True)
    rv2 = client.get('/channels', follow_redirects=True)
    assert rv.status_code == 200
    assert rv2.status_code == 200
    assert rv.data == rv2.data


def test_callback_wrong_state(client):
    """ Wrong channel id given on callback -> redirected to channels """
    login(client, "admin")
    rv = client.get('/callback_In?state=wrong&code=42', follow_redirects=True)
    rv1 = client.get('/callback_In?state=1000000&code=42', follow_redirects=True)
    rv2 = client.get('/channels', follow_redirects=True)
    assert rv.status_code == 200
    assert rv1.status_code == 200
    assert rv2.status_code == 200
    assert rv1.data == rv2.data
    assert rv.data == rv2.data


def test_callback_state_not_In(client):
    """ Received channel id is not a linkedin channel -> redirected to channels """
    login(client, "admin")
    create_channel(client, 'test_In_mail', 'mail')
    c = get_channel(client, 'test_In_mail')

    rv = client.get('/callback_In?state=' + str(c.id) + '&code=42', follow_redirects=True)
    rv2 = client.get('/channels', follow_redirects=True)
    assert rv.status_code == 200
    assert rv2.status_code == 200
    assert rv.data == rv2.data

    delete_channel(client, c.id, c.name)
