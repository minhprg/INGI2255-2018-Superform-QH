# To run : Be sure to be in Superform/superform folder and then 'pytest -v' in your terminal
import os
import tempfile

import pytest
from pathlib import Path

from sqlalchemy import desc

from superform import app, db, Post
from superform.models import Channel, Publishing, State, Moderation
from superform.utils import datetime_converter, str_converter


root, current_dir = os.path.split(os.path.dirname(__file__))
root = root + "/plugins/rssfeeds/"


def clear_data(session):
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        session.execute(table.delete())
    session.commit()


def del_file(path):
    for item in path:
        if Path(item).exists():
            os.remove(item)


def get_moderation(client, post, chan, pub):
    return client.get('/moderate/' + str(post.id) + '/' + str(chan.id), data=dict(pub=pub), follow_redirects=True)


def get_rework_publishing(client, post, chan, pub):
    return client.get('/edit/' + str(post.id) + '/' + str(chan.id), data=dict(pub=pub), follow_redirects=True)


def post_abort_rework_publishing(client, post, chan):
    return client.post('/edit/' + str(post.id) + '/' + str(chan.id) + '/abort_edit_publishing', follow_redirects=True)


def get_view_feedback(client, post, chan):
    return client.get('/feedback/' + str(post.id) + '/' + str(chan.id), follow_redirects=True)


def get_view_publishing(client, post, chan):
    return client.get('/publishing/' + str(post.id) + '/' + str(chan.id), follow_redirects=True)


def post_validate_rework_publishing(client, pub, chan):
    return client.post('/edit/' + str(pub.post_id) + '/' + str(chan.id) + '/validate_edit_publishing',
                       data=dict(titlepost=pub.title, descrpost=pub.description, linkurlpost=pub.link_url,
                                 imagepost=pub.image_url, datefrompost=str_converter(pub.date_from),
                                 dateuntilpost=str_converter(pub.date_until)), follow_redirects=True)


def post_refuse_publishing(client, post, chan, commentpub):
    return client.post('/moderate/' + str(post.id) + '/' + str(chan.id) + '/refuse_publishing',
                       data=dict(titlepost=post.title, descrpost=post.description, linkurlpost=post.link_url,
                                 imagepost=post.image_url, datefrompost=post.date_from,
                                 dateuntilpost=post.date_until, commentpub=commentpub),
                       follow_redirects=True)


def post_validate_publishing(client, post, chan, commentpub):
    return client.post('/moderate/' + str(post.id) + '/' + str(chan.id) + '/validate_publishing',
                       data=dict(titlepost=post.title, descrpost=post.description, linkurlpost=post.link_url,
                                 imagepost=post.image_url, datefrompost=str_converter(post.date_from),
                                 dateuntilpost=str_converter(post.date_until), commentpub=commentpub),
                       follow_redirects=True)


def create(client):
    post = Post(user_id='myself', title='title_post', description='descr_post', link_url='link_post',
                image_url='image_post',
                date_from=datetime_converter('2017-06-02'), date_until=datetime_converter('2017-06-03'))
    db.session.add(post)
    db.session.commit()
    chan = Channel(name='rss', id=-1, module='superform.plugins.rss',
                   config='{"feed_title": "test_title", "feed_description": "test_desc"}')
    db.session.add(chan)
    db.session.commit()
    pub = Publishing(post_id=post.id, channel_id=chan.id, state=0, title=post.title, description=post.description,
                     link_url=post.link_url, image_url=post.image_url,
                     date_from=post.date_from, date_until=post.date_until)
    db.session.add(pub)
    db.session.commit()

    return post, chan, pub


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

    path = root + "-1.xml"
    del_file([path])

    clear_data(db.session)
    os.close(db_fd)
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///superform.db"


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


# Testing Functions


def test_access_moderate_publishing(client):
    login(client, "myself")
    post, chan, pub = create(client)

    response = get_moderation(client, post, chan, pub)
    assert response.status_code == 200

    pub.date_from = datetime_converter(pub.date_from)
    pub.date_until = datetime_converter(pub.date_until)


def test_validate_publishing_with_feedback(client):
    login(client, 'myself')
    post, chan, pub = create(client)

    response = post_validate_publishing(client, post, chan, "Test validation")
    assert response.status_code == 200

    pub1 = db.session.query(Publishing).filter(Publishing.post_id == post.id and Publishing.channel_id == chan.id).first()
    assert pub1.state == State.VALIDATED.value

    mod = db.session.query(Moderation).filter(Moderation.channel_id == chan.id, Moderation.post_id == post.id).first()
    assert mod.message == "Test validation"

    path = root + "-1.xml"
    del_file([path])


def test_validate_publishing_without_feedback(client):
    login(client, 'myself')
    post, chan, pub = create(client)

    response = post_validate_publishing(client, post, chan, "")
    assert response.status_code == 200

    pub1 = db.session.query(Publishing).filter(Publishing.post_id == post.id and Publishing.channel_id == chan.id).first()
    assert pub1.state == State.VALIDATED.value

    mod = db.session.query(Moderation).filter(Moderation.channel_id == chan.id, Moderation.post_id == post.id).first()
    assert mod.message == ""

    path = root + "-1.xml"
    del_file([path])


def test_refuse_publishing_with_feedback(client):
    login(client, 'myself')
    post, chan, pub = create(client)

    response = post_refuse_publishing(client, post, chan, "Test feedback")
    assert response.status_code == 200

    pub1 = db.session.query(Publishing).filter(
        Publishing.post_id == post.id and Publishing.channel_id == chan.id).first()
    assert pub1.state == State.REFUSED.value

    mod = db.session.query(Moderation).filter(Moderation.channel_id == chan.id, Moderation.post_id == post.id).first()
    assert mod.message == "Test feedback"

    path = root + "-1.xml"
    del_file([path])


def test_refuse_publishing_without_feedback(client):
    login(client, 'myself')
    post, chan, pub = create(client)

    response = post_refuse_publishing(client, post, chan, "")
    assert response.status_code == 200

    pub.date_from = datetime_converter(pub.date_from)
    pub.date_until = datetime_converter(pub.date_until)

    pub1 = db.session.query(Publishing).filter(
        Publishing.post_id == post.id and Publishing.channel_id == chan.id).first()
    assert pub1.state == State.NOTVALIDATED.value

    mod = db.session.query(Moderation).filter(Moderation.channel_id == chan.id, Moderation.post_id == post.id).first()
    assert mod is None

    path = root + "-1.xml"
    del_file([path])


def test_access_rework_publishing(client):
    login(client, 'myself')
    post, chan, pub = create(client)

    response = post_validate_publishing(client, post, chan, "")
    assert response.status_code == 200

    response = get_rework_publishing(client, post, chan, pub)
    assert response.status_code == 200


def test_publish_rework_publishing(client):
    login(client, 'myself')
    post, chan, pub = create(client)

    response = post_refuse_publishing(client, post, chan, "Refused")
    assert response.status_code == 200

    pub.title = "New title"
    db.session.commit()

    post = db.session.query(Post).filter(Post.id == post.id).first()
    response = post_validate_rework_publishing(client, pub, chan)
    assert response.status_code == 200

    new_post = db.session.query(Post).order_by(desc(Post.id)).first()
    assert new_post.id > post.id

    old_pub = db.session.query(Publishing).filter(Publishing.channel_id == chan.id, Publishing.post_id == post.id).first()
    new_pub = db.session.query(Publishing).filter(Publishing.channel_id == chan.id, Publishing.post_id == new_post.id).first()
    assert old_pub.state == State.OUTDATED.value
    assert new_pub.state == State.NOTVALIDATED.value
    assert new_pub.title == "New title"


def test_abort_rework_publishing(client):
    login(client, 'myself')
    post, chan, pub = create(client)

    response = post_refuse_publishing(client, post, chan, "Refused")
    assert response.status_code == 200

    response = post_abort_rework_publishing(client, post, chan)
    assert response.status_code == 200

    new_pub = db.session.query(Publishing).filter(Publishing.post_id == pub.post_id,
                                                  Publishing.channel_id == pub.channel_id).first()
    assert new_pub == pub


def test_view_feedback(client):
    login(client, 'myself')
    post, chan, pub = create(client)

    response = post_validate_publishing(client, post, chan, "")
    assert response.status_code == 200

    response = get_view_feedback(client, post, chan)
    assert response.status_code == 200

    pub.date_from = datetime_converter(pub.date_from)
    pub.date_until = datetime_converter(pub.date_until)

    mod = db.session.query(Moderation).filter(Moderation.post_id == post.id, Moderation.channel_id == chan.id).first()
    assert mod.message == ""


def test_view_publishing(client):
    login(client, 'myself')
    post, chan, pub = create(client)

    response = get_view_publishing(client, post, chan)
    assert response.status_code == 200

    pub.date_until = datetime_converter(pub.date_until)
    pub.date_from = datetime_converter(pub.date_from)

    new_pub = db.session.query(Publishing).filter(Publishing.post_id == post.id, Publishing.channel_id == chan.id).first()
    assert new_pub.state == pub.state and new_pub.title == pub.title and new_pub.description == pub.description
