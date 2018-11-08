# To run : Be sure to be in Superform/superform folder and then 'pytest -v' in your terminal
#export PYTHONPATH=~/PycharmProjects/INGI2255-2018-Superform-QH/superform
import datetime
import os
import tempfile

import pytest

from superform import app, db
from superform.models import Authorization, Channel
from superform import app, db, Post, User, Publishing
from superform.users import  is_moderator, get_moderate_channels_for_user,channels_available_for_user

chan_id_1 = -1  # Should be created
chan_id_2 = -1  # Shouldn't be created

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
            if login is "myself":
                sess["admin"] = True
            else:
                sess["admin"] = False

            sess["logged_in"] = True
            sess["first_name"] = "gen_login"
            sess["name"] = "myname_gen"
            sess["email"] = "hello@genemail.com"
            sess['user_id'] = login


def test_new_channel_as_admin(client):
    global chan_id_1, chan_id_2
    login(client, "myself")

    # Create a test channel
    client.post("/channels", data={'@action': 'new', 'name': 'test_channel_gcal_1', 'module': 'gcal'})
    chan = db.session.query(Channel).all()[-1]
    assert chan
    chan_id_1 = chan.id
    assert chan_id_1 >= 0

    # Configure the channel
    client.post("/configure/" + str(chan_id_1), data={'creds': 'test'})
    chan = db.session.query(Channel).filter(Channel.id == chan_id_1).first()
    assert chan
    # chan_creds = chan.config
    # TODO test creds correctly saved


def test_new_channel_no_admin(client):
    global chan_id_1, chan_id_2
    login(client, "alterego")

    # Create a test channel
    client.post("/channels", data={'@action': 'new', 'name': 'test_channel_gcal_2', 'module': 'gcal'})
    chan = db.session.query(Channel).all()[-1]
    assert chan
    chan_id_2 = chan.id
    assert chan_id_2 == chan_id_1
    chan_id_2 = -1

    # Configure the channel
    client.post("/configure/" + str(chan_id_2), data={'creds': 'test'})
    chan = db.session.query(Channel).filter(Channel.id == chan_id_2).first()
    assert not chan


def test_new_publish_gcal(client):
    global chan_id_1, chan_id_2
    login(client, "myself")

    title = 'A test new gcal post'
    description = 'Dome random content, just what we need for a test'

    # publish a not yet expired post
    d = datetime.date.today()
    d += datetime.timedelta(1)
    client.post('/new', data=dict(titlepost=title, descriptionpost=description,
                                  datefrompost=d.strftime("%Y-%m-%dT%H:%M"),
                                  dateuntilpost=d.strftime("%Y-%m-%dT%H:%M")))
    client.post('/publish',
                data={'chan_option_' + str(chan_id_1): "chan_option_0", 'titlepost': title,
                      'descriptionpost': description, 'datefrompost': d.strftime("%Y-%m-%dT%H:%M"),
                      'dateuntilpost': d.strftime("%Y-%m-%dT%H:%M")})

    post = db.session.query(Post).filter(Post.title == title)\
        .filter(Post.description == description).first()
    pub = db.session.query(Publishing).filter(Publishing.title == title)\
        .filter(Publishing.description == description).first()
    assert post
    assert pub
    title = post.title
    assert title == 'A test new gcal post'
    title = pub.title
    assert title == 'A test new gcal post'
    db.session.delete(post)
    db.session.delete(pub)
    db.session.commit()


def test_delete_channel_no_admin(client):
    global chan_id_1, chan_id_2
    login(client, "alterego")

    client.post("/channels", data={'@action': 'delete', 'id': chan_id_1})

    chan = db.session.query(Channel).filter(Channel.id == chan_id_1).first()
    assert chan


def test_delete_channel_as_admin(client):
    global chan_id_1, chan_id_2
    login(client, "myself")

    print(chan_id_1)
    client.post("/channels", data={'@action': 'delete', 'id': chan_id_1})

    chan = db.session.query(Channel).filter(Channel.id == chan_id_1).first()
    assert not chan
