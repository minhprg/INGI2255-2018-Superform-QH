import os
import tempfile

import pytest

from superform import app, db, Post
from superform.models import Channel, Publishing
from superform.utils import datetime_converter

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
            if login is not "myself":
                sess["admin"] = True
            else:
                sess["admin"] = False

            sess["logged_in"] = True
            sess["first_name"] = "gen_login"
            sess["name"] = "myname_gen"
            sess["email"] = "hello@genemail.com"
            sess['user_id'] = login


def prefill_db(client):
    post = Post(user_id='myself', title='title_post', description='descr_post', link_url='link_post',
                image_url='image_post',
                date_from=datetime_converter('2020-01-01'), date_until=datetime_converter('2020-01-01'))
    db.session.add(post)
    db.session.commit()
    chan = Channel(name='my_mail', id=-1, module='superform.plugins.mail',
                   config='{"sender":"mail@example.com", "receiver":"mail@example.com"}')
    db.session.add(chan)
    db.session.commit()
    pub = Publishing(post_id=post.id, channel_id=chan.id, state=0, title=post.title, description=post.description,
                     link_url=post.link_url, image_url=post.image_url,
                     date_from=post.date_from, date_until=post.date_until)
    db.session.add(pub)
    db.session.commit()

    return post, chan, pub

def test_modif_post(client):
    login(client, "myself")
    post, chan, pub = prefill_db(client)
    data1 = {'datefrompost': '2021-01-01', 'dateuntilpost': '2021-01-01', 'descriptionpost': post.description,
             'titlepost' : 'new title', 'linkurlpost': post.link_url,'imagepost': post.image_url}
    rv = client.post('/publish/edit/'+str(post.id), data=data1, follow_redirects=True)
    assert rv.status_code == 200
    po = db.session.query(Post).filter(Post.id == post.id).first()
    assert po.date_from == datetime_converter('2021-01-01')
    assert po.date_until == datetime_converter('2021-01-01')
    assert po.description == post.description
    assert po.title == 'new title'
    assert po.link_url == post.link_url
    assert po.image_url == post.image_url

def test_modif_publishing(client):
    login(client, "myself")
    post, chan, pub = prefill_db(client)
    data1 = {'datefrompost': '2021-01-01', 'dateuntilpost': '2021-01-01', 'descriptionpost': post.description,
             'titlepost' : 'new title', 'linkurlpost': post.link_url,'imagepost': post.image_url,
             'chan_option_'+str(chan.id) : chan.id, chan.name + '_datefrompost': '2022-01-01',
             chan.name + '_dateuntilpost': '2022-01-01', chan.name + '_descriptionpost': post.description,
             chan.name + '_titlepost': 'new title spec for chan', chan.name + '_linkurlpost': post.link_url,
             chan.name + '_imagepost': post.image_url}
    rv = client.post('/publish/edit/'+str(post.id), data=data1, follow_redirects=True)
    assert rv.status_code == 200
    po = db.session.query(Post).filter(Post.id == post.id).first()
    assert po.date_from == datetime_converter('2021-01-01')
    assert po.date_until == datetime_converter('2021-01-01')
    assert po.description == post.description
    assert po.title == 'new title'
    assert po.link_url == post.link_url
    assert po.image_url == post.image_url
    pu = db.session.query(Publishing).filter(Publishing.post_id == post.id, Publishing.channel_id == chan.id).first()
    assert pu.date_from == datetime_converter('2022-01-01')
    assert pu.date_until == datetime_converter('2022-01-01')
    assert pu.description == post.description
    assert pu.title == 'new title spec for chan'
    assert pu.link_url == post.link_url
    assert pu.image_url == post.image_url