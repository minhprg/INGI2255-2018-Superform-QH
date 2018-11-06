import datetime
import os
import tempfile

import pytest

from superform import app, db
from superform.plugins import facebook


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


def test_valid_module(client):
    try:
        from superform.plugins.facebook import run
    except ImportError:
        assert False

    assert 'FIELDS_UNAVAILABLE' in dir(facebook)
    assert 'CONFIG_FIELDS' in dir(facebook)


def test_get_url_for_token():
    assert facebook.get_url_for_token(1234) == 'https://www.facebook.com/v2.7/dialog/oauth?' \
                                               'client_id=1672680826169132' \
                                               '&redirect_uri=https%3A%2F%2F127.0.0.1%3A5000%2Fcallback_fb' \
                                               '&scope=manage_pages%2Cpublish_pages' \
                                               '&state=1234'


def test_get_page():
    assert facebook.get_page('bla') == ['error']