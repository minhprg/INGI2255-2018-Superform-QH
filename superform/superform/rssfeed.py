from flask import Blueprint, make_response, render_template
from pathlib import Path

feed_viewer_page = Blueprint('rssfeed', __name__)


def tester():
    print(Path(".").absolute())


@feed_viewer_page.route('/rss/<string:feed_url>', methods=["GET"])
def get_rss_feed(feed_url):
    full_path = "./superform/plugins/rssfeeds/" + feed_url
    folder = Path("./superform/plugins/rssfeeds/")
    print(str(folder.exists()) + " " + str(folder.absolute()))
    file = Path(full_path)
    resp = None
    if file.exists():
        # Ok !
        with open(file, 'r') as f:
            xml_file = f.read()
        resp = make_response(xml_file, 200)
        resp.headers['Content-Type'] = 'text/xml' #'application/rss+xml'
    else:
        resp = make_response(render_template('404.html'), 404)
    return resp
