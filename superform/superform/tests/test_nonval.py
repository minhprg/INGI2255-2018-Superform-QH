# To run : Be sure to be in Superform/superform folder and then 'pytest -v' in your terminal
import datetime
import os
import tempfile

import pytest

from superform.models import Channel, Publishing
from superform import app, db, Post
from superform.utils import datetime_converter, login_required
from superform.publishings import create_a_publishing, refuse_publishing, validate_publishing


class Form:
    def get(self):
        return None


@pytest.fixture(scope='module')
def global_data():
    return {'pub_post_id': 0, 'pub_channel_id': 0}


@pytest.fixture
def client():
    app.app_context().push()
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['SERVER_NAME'] = ""
    client = app.test_client()

    with app.app_context():
        db.create_all()

    yield client

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])


@pytest.fixture(autouse=True, scope='session')
def my_fixture():
    # setup_stuff
    yield
    # teardown_stuff
    # delete created post and related publishing
    #print("pytest.pub_post_id: ", pytest.pub_post_id)
    pub = Publishing.query.get((pytest.pub_post_id, pytest.pub_channel_id))
    post = Post.query.get(pytest.pub_post_id)
    db.session.delete(pub)
    db.session.commit()
    db.session.delete(post)
    db.session.commit()


def login(client, login):
    with client as c:
        with c.session_transaction() as sess:
            sess["admin"] = True
            sess["logged_in"] = True
            sess["first_name"] = "gen_login"
            sess["name"] = "myname_gen"
            sess["email"] = "hello@genemail.com"
            sess['user_id'] = "myself"


## Testing Functions ##


def test_publishing_state_is_zero(global_data, client):
    post = Post(user_id='myself', title='title_post', description='descr_post', link_url='link_post',
                image_url='image_post',
                date_from=datetime_converter('2017-06-02'), date_until=datetime_converter('2017-06-03'))
    db.session.add(post)
    db.session.commit()
    chan = Channel(name='rss', id='1')
    #form = Form
    #pub = create_a_publishing(post, chan, form)
    pub = Publishing(post_id=post.id, channel_id=chan.id, state=0, title=post.title, description=post.description,
                     link_url=post.link_url, image_url=post.image_url,
                     date_from=post.date_from, date_until=post.date_until)
    db.session.add(pub)
    db.session.commit()
    pytest.pub_post_id = pub.post_id
    pytest.pub_channel_id = pub.channel_id
    p = Publishing.query.get((pytest.pub_post_id, pytest.pub_channel_id))
    assert p.state == 0


# marche pas
def test_refuse_publishing(global_data, client):
    #with app.app_context('/moderate/<int:id>/<string:idc>/refuse_publishing', method=["POST"]):
        refuse_publishing(pytest.pub_post_id, pytest.pub_channel_id)
        p = Publishing.query.get((pytest.pub_post_id, pytest.pub_channel_id))
        assert p.state == 3



"""
# marche pas
def test_validate_publishing(global_data, client):
    validate_publishing(pytest.pub_post_id, pytest.pub_channel_id)
    p = Publishing.query.get((pytest.pub_post_id, pytest.pub_channel_id))
    assert p.state == 1
    
"""
