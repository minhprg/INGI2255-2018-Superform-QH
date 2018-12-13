import os
from pathlib import Path

from flask import Blueprint, make_response, render_template

feed_viewer_page = Blueprint('rssfeed', __name__)


@feed_viewer_page.route('/rss/<string:feed_url>', methods=["GET"])
def get_rss_feed(feed_url):
    """
    Get the rss feed
    :param feed_url: the url of the rss feed
    :return: response to the request
    """
    rssfeed_path = os.path.dirname(__file__)
    if '.xml' not in feed_url:
        feed_url += '.xml'
    file = Path(rssfeed_path + "/plugins/rssfeeds/" + feed_url)
    if file.exists():
        # Ok !
        with open(file, 'r') as f:
            xml_file = f.read()
        resp = make_response(xml_file, 200)
        resp.headers['Content-Type'] = 'text/xml' #'application/rss+xml'
    else:
        resp = make_response(render_template('404.html'), 404)
    return resp
