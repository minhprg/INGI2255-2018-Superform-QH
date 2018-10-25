
import PyRSS2Gen
import datetime
import json

FIELDS_UNAVAILABLE = ["date_from", "date_until", "image"]
CONFIG_FIELDS = ["feedUrl"]
rss = None


def createInitialFeed(channel_config):
    json_data = json.loads(channel_config)
    destination = json_data['feedUrl']

    global rss
    rss = PyRSS2Gen.RSS2(
        title="Superform's feed",
        link="http://localhost:8888/rssfeed.rss",
        description="The RSS feed of Superform",
        items=[]
    )
    rss.write_xml(open(destination, "w"))

    return rss


def run(publishing, channel_config):
    json_data = json.loads(channel_config)
    destination = json_data["feedUrl"]

    global rss
    if rss is None:
        rss = createInitialFeed(channel_config)

    pubDate = datetime.datetime.now()

    item = PyRSS2Gen.RSSItem(
                title=publishing.title,
                link=publishing.link_url,
                description=publishing.description,
                pubDate=pubDate)

    rss.items.insert(0, item)
    for post in rss.items:
        if post.pubDate + datetime.timedelta(365) < pubDate:
            rss.items.remove(post)
    rss.write_xml(open(destination, "w"))
