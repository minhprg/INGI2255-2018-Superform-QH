import datetime
import os
import tempfile

import pytest

from superform.models import Channel
from superform import app, db, Post, Publishing


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


def test_new_records(client):
    login(client, "myself")

    # create a test channel
    client.post("/channels", data={'@action': 'new', 'name': 'test_channel', 'module': 'mail'})
    chan_id = db.session.query(Channel).all()[-1].id

    # publish a not yet expired post
    d = datetime.date.today()
    d += datetime.timedelta(1)
    client.post('/new', data=dict(titlepost='A test_new_record post', descrpost="A description",
                                  datefrompost=d.strftime("%Y-%m-%d"),
                                  timefrompost=d.strftime("%H:%M"),
                                  dateuntilpost=d.strftime("%Y-%m-%d"),
                                  timeuntilpost=d.strftime("%H:%M")))
    client.post('/publish', data={'chan_option_' + str(chan_id): "chan_option_0",
                                  'titlepost': 'A test_new_record publishing', 'descrpost': "A description",
                                  'datefrompost': d.strftime("%Y-%m-%d"),
                                  'timefrompost': d.strftime("%H:%M"),
                                  'dateuntilpost': d.strftime("%Y-%m-%d"),
                                  'timeuntilpost': d.strftime("%H:%M")})

    # accept last publication
    post = db.session.query(Post).filter().all()
    last_add = post[-1]
    db.session.query(Publishing).filter(Publishing.post_id == last_add.id).update({Publishing.state: 1})
    db.session.commit()

    # update archived posts
    client.get('/records', data=dict())
    archived = db.session.query(Publishing).filter(Publishing.state == 2).all()
    # must not be in the database as archived
    for arch in archived:
        if arch.post_id == last_add.id:
            assert False
    db.session.query(Publishing).filter(Publishing.post_id == last_add.id).delete()
    db.session.commit()

    # publish a expired post
    db.session.query(Post).filter(Post.id == last_add.id).delete()
    d -= datetime.timedelta(3)
    client.post('/new', data=dict(titlepost='A test_new_record post', descrpost="A description",
                                  linkurlpost="http://www.test.com", imagepost="image.jpg",
                                  datefrompost=d.strftime("%Y-%m-%d"),
                                  timefrompost=d.strftime("%H:%M"),
                                  dateuntilpost=d.strftime("%Y-%m-%d"),
                                  timeuntilpost=d.strftime("%H:%M")))
    client.post('/publish', data={'chan_option_' + str(chan_id): "chan_option_0",
                                  'titlepost': 'A test_new_record publishing', 'descrpost': "A description",
                                  'datefrompost': d.strftime("%Y-%m-%d"),
                                  'timefrompost': d.strftime("%H:%M"),
                                  'dateuntilpost': d.strftime("%Y-%m-%d"),
                                  'timeuntilpost': d.strftime("%H:%M")})
    # accept last publication
    post = db.session.query(Post).filter().all()
    last_add = post[-1]
    db.session.query(Publishing).filter(Publishing.post_id == last_add.id).update({Publishing.state: 1})
    db.session.commit()

    client.get('/records', data=dict())
    archived = db.session.query(Publishing).filter(Publishing.state == 2)\
        .filter(Publishing.post_id == last_add.id).all()
    # must be in the database as archived
    assert len(archived) > 0

    db.session.query(Publishing).filter(Publishing.post_id == last_add.id).delete()
    db.session.commit()

    db.session.query(Post).filter(Post.title == 'A test_new_record post').delete()
    db.session.commit()
    db.session.query(Post).filter(Post.title == 'A test_new_record publishing').delete()
    db.session.commit()
    client.post("/channels", data={'@action': 'delete', 'id': chan_id})


def test_delete_record(client):
    login(client, "myself")

    # create a test channel
    client.post("/channels", data={'@action': 'new', 'name': 'test_channel', 'module': 'mail'})
    chan_id = db.session.query(Channel).all()[-1].id

    d = datetime.date.today()
    d -= datetime.timedelta(1)
    client.post('/new', data=dict(titlepost='A test_delete_record post', descrpost="A description",
                                  linkurlpost="http://www.test.com", imagepost="image.jpg",
                                  datefrompost=d.strftime("%Y-%m-%d"),
                                  timefrompost=d.strftime("%H:%M"),
                                  dateuntilpost=d.strftime("%Y-%m-%d"),
                                  timeuntilpost=d.strftime("%H:%M")))
    client.post('/publish', data={'chan_option_' + str(chan_id): "chan_option_0",
                                  'titlepost': 'A test_delete_record publishing', 'descrpost': "A description",
                                  'datefrompost': d.strftime("%Y-%m-%d"),
                                  'timefrompost': d.strftime("%H:%M"),
                                  'dateuntilpost': d.strftime("%Y-%m-%d"),
                                  'timeuntilpost': d.strftime("%H:%M")})

    # accept last publication
    post = db.session.query(Post).filter().all()
    last_add = post[-1]
    db.session.query(Publishing).filter(Publishing.post_id == last_add.id).update({Publishing.state: 1})
    db.session.commit()

    client.get('/records', data=dict())

    archived = db.session.query(Publishing).filter(Publishing.state == 2)\
        .filter(Publishing.post_id == last_add.id).all()
    # must be in the database as archived
    assert len(archived) > 0

    client.post("/records", data={"@action": "delete", "id": archived[-1].post_id, "idc": archived[-1].channel_id,
                                  "follow_redirects": True})

    archived = db.session.query(Publishing).filter(Publishing.state == 2)\
        .filter(Publishing.post_id == last_add.id).all()
    assert not archived
    db.session.query(Post).filter(Post.title == 'A test_delete_record post').delete()
    db.session.commit()
    db.session.query(Post).filter(Post.title == 'A test_delete_record publishing').delete()
    db.session.commit()
    client.post("/channels", data={'@action': 'delete', 'id': chan_id})
