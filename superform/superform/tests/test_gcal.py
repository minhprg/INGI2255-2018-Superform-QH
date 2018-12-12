# To run : Be sure to be in Superform/superform folder and then 'pytest -v' in your terminal
# export PYTHONPATH=~/PycharmProjects/INGI2255-2018-Superform-QH/superform
import datetime
import os
import tempfile

import pytest

from superform.models import Channel
from superform import app, db, Post, Publishing

chan_id_1 = -1  # Should be created
chan_id_2 = -1  # Shouldn't be created


def clear_data(session):
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        session.execute(table.delete())
    session.commit()


@pytest.fixture
def client():
    app.app_context().push()

    db_fd, database = tempfile.mkstemp()
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///"+database+".db"
    app.config['TESTING'] = True
    client = app.test_client()

    with app.app_context():
        db.create_all()

    yield client

    clear_data(db.session)
    os.close(db_fd)
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///superform.db"


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
    calendar_id = 'test'
    client_id = 'test'
    client_secret = 'test'
    client.post("/configure/" + str(chan_id_1), data={"calendar id": calendar_id,
                                                      "clientID": client_id,
                                                      "clientSecret": client_secret})
    chan = db.session.query(Channel).filter(Channel.id == chan_id_1).first()
    assert chan

    # Check channel configuration
    chan_creds = chan.config
    assert chan_creds == "{\"calendar id\" : \"" + calendar_id \
        + "\",\"clientID\" : \"" + client_id \
        + "\",\"clientSecret\" : \"" + client_secret + "\"}"


def test_new_channel_no_admin(client):
    global chan_id_1, chan_id_2
    test_new_channel_as_admin(client)
    login(client, "alterego")

    # Create a test channel
    client.post("/channels", data={'@action': 'new', 'name': 'test_channel_gcal_2', 'module': 'gcal'})
    chan = db.session.query(Channel).all()[-1]
    assert chan
    chan_id_2 = chan.id
    assert chan_id_2 == chan_id_1
    chan_id_2 = -1

    # Configure the channel
    client.post("/configure/" + str(chan_id_2), data={"calendar id": 'test',
                                                      "clientID": 'test',
                                                      "clientSecret": 'test'})
    chan = db.session.query(Channel).filter(Channel.id == chan_id_2).first()
    assert not chan


def test_new_publish_gcal(client):
    global chan_id_1, chan_id_2
    test_new_channel_as_admin(client)
    login(client, "myself")

    chan = db.session.query(Channel).filter(Channel.id == chan_id_1).first()
    assert chan

    title = 'A test new gcal post'
    description = 'Some random content, just what we need for a test'

    # Create a post
    d = datetime.date.today()
    d += datetime.timedelta(1)
    client.post('/new', data=dict(titlepost=title, descriptionpost=description,
                                  datefrompost=d.strftime("%Y-%m-%d"),
                                  timefrompost=d.strftime("%H:%M"),
                                  dateuntilpost=d.strftime("%Y-%m-%d"),
                                  timeuntilpost=d.strftime("%H:%M")))
    post = db.session.query(Post).filter(Post.title == title) \
        .filter(Post.description == description).all()[-1]
    assert post
    assert title == post.title

    # Publish a post
    client.post('/publish',
                data={'chan_option_' + str(chan.id): "chan_option_0", 'titlepost': title,
                      'descriptionpost': description,
                      'datefrompost': d.strftime("%Y-%m-%d"),
                      'timefrompost': d.strftime("%H:%M"),
                      'dateuntilpost': d.strftime("%Y-%m-%d"),
                      'timeuntilpost': d.strftime("%H:%M")})
    pub = db.session.query(Publishing).filter(Publishing.title == title) \
        .filter(Publishing.description == description).all()[-1]
    assert pub
    assert title == pub.title

    # Moderate a post
    print(chan_id_1)
    print(chan.id)
    client.post('/moderate/' + str(pub.post_id) + '/' + str(chan.id), data={'titlepost': title,
                                                           'descrpost': description,
                                  'datefrompost': d.strftime("%Y-%m-%d"),
                                  'timefrompost': d.strftime("%H:%M"),
                                  'dateuntilpost': d.strftime("%Y-%m-%d"),
                                  'timeuntilpost': d.strftime("%H:%M")})

    # Cleaning up
    db.session.delete(post)
    db.session.delete(pub)
    db.session.commit()


def test_delete_channel_no_admin(client):
    global chan_id_1, chan_id_2
    test_new_channel_as_admin(client)
    login(client, "alterego")

    client.post("/channels", data={'@action': 'delete', 'id': chan_id_1})

    chan = db.session.query(Channel).filter(Channel.id == chan_id_1).first()
    assert chan


def test_delete_channel_as_admin(client):
    global chan_id_1, chan_id_2
    login(client, "myself")

    client.post("/channels", data={'@action': 'delete', 'id': chan_id_1})

    chan = db.session.query(Channel).filter(Channel.id == chan_id_1).first()
    assert not chan
