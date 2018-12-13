import os
import tempfile
from urllib.parse import parse_qs

import pytest
from pytest_localserver.http import WSGIServer

from superform import app, db, Publishing
from superform.plugins import wiki
from superform.plugins.wiki import format_title, format_text
from superform.tests.test_archival import clear_data
from superform.utils import StatusCode


@pytest.fixture
def testserver(request):
    """Defines the testserver funcarg"""
    server = WSGIServer(application=simple_app)
    server.start()
    request.addfinalizer(server.stop)
    return server


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


def test_format_title():
    title = 'my-super, title, with ;lot <of \/fails \\like \nthis ?or @this &and %that'

    assert format_title(title) == 'mysupertitlewithlotoffailslikethisorthisandthat'


def test_format_text():
    title, description = 'my title', 'my description'

    assert format_text(title, description) == '(:title my title:)my description'


def simple_app(environ, start_response):
    """Simplest possible WSGI application"""
    response = "b'(:title test wiki:)This is a test description feed'"
    username = "b'myself'"
    password = "b'myself'"
    status = '200 OK'
    assert environ['PATH_INFO'] == '/News/testwiki-1-1'
    response_body = "Hello World!\n"
    response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', str(len(response_body)))]
    if environ['REQUEST_METHOD'] == 'POST':
        resp = environ['wsgi.input'].read(int(environ['CONTENT_LENGTH']))
        d = parse_qs(resp)
        for item in d.items():
            if str(item[0]) == "b'text'" and str(item[1][0]) != response:
                status = '500'
            elif str(item[0]) == "b'authid'" and str(item[1][0]) != username:
                status = '500'
            elif str(item[0]) == "b'authpw'" and str(item[1][0]) != password:
                status = '500'

    start_response(status, response_headers)
    return [response_body.encode()]


def test_wiki_post(client, testserver):
    login(client, 'myself')

    pub = Publishing(title="test wiki", description="This is a test description feed", link_url="www.facebook.com",
                     channel_id=1, post_id=1)

    conf = "{\"username\": \"myself\", \"password\": \"myself\", \"base_url\": \"" + testserver.url + "\"}"

    status_code, _, _ = wiki.run(pub, conf)

    assert status_code == StatusCode.OK


def test_wiki_post_bad_username(client, testserver):
    login(client, "myself")

    pub = Publishing(title="test wiki", description="This is a test description feed", link_url="www.facebook.com",
                     channel_id=1, post_id=1)

    conf = "{\"username\": \"bad\", \"password\": \"myself\", \"base_url\": \"" + testserver.url + "\"}"

    status_code, error_message, _ = wiki.run(pub, conf)

    assert status_code == StatusCode.ERROR
    assert error_message == "Bad username or password"


def test_wiki_bad_base_url(client):
    login(client, "myself")

    pub = Publishing(title="test wiki", description="This is a test description feed", link_url="www.facebook.com",
                     channel_id=1, post_id=1)

    conf = "{\"username\": \"myself\", \"password\": \"bad\", \"base_url\": \"server.down\"}"

    status_code, error_message, _ = wiki.run(pub, conf)

    assert status_code == StatusCode.ERROR
    assert error_message == "Wrong base_url, please check the format again"


def test_wiki_server_down(client):
    login(client, "myself")

    pub = Publishing(title="test wiki", description="This is a test description feed", link_url="www.facebook.com",
                     channel_id=1, post_id=1)

    conf = "{\"username\": \"myself\", \"password\": \"bad\", \"base_url\": \"http://server.down\"}"

    status_code, error_message, _ = wiki.run(pub, conf)

    assert status_code == StatusCode.ERROR
    assert error_message == "Couldn't connect to server"


def test_wiki_post_bad_password(client, testserver):
    login(client, "myself")

    pub = Publishing(title="test wiki", description="This is a test description feed", link_url="www.facebook.com",
                     channel_id=1, post_id=1)

    conf = "{\"username\": \"myself\", \"password\": \"bad\", \"base_url\": \"" + testserver.url + "\"}"

    status_code, error_message, _ = wiki.run(pub, conf)

    assert status_code == StatusCode.ERROR
    assert error_message == "Bad username or password"
