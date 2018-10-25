import PyRSS2Gen
import datetime
import json
from pathlib import Path
from lxml import etree


FIELDS_UNAVAILABLE = ["date_from", "date_until", "image"]
CONFIG_FIELDS = ["feedUrl"]
rss = None


def createInitialFeed():

    global rss
    rss = PyRSS2Gen.RSS2(
        title="Superform's feed",
        link="http://localhost:8888/rssfeed.rss",
        description="The RSS feed of Superform",
        items=[]
    )

    return rss


def run(publishing, channel_config):
    global rss

    json_data = json.loads(channel_config)
    destination = json_data["feedUrl"]

    file = Path(destination)

    if not file.exists():
        rss = createInitialFeed()
    else:
        tree = etree.parse(destination)

        if rss is None:
            rss = createInitialFeed()

            title = list()
            link = list()
            description = list()
            pubDate = list()

            for attrib in tree.xpath("/rss/channel/item/title"):
                title.append(attrib.text)

            for attrib in tree.xpath("/rss/channel/item/link"):
                link.append(attrib.text)

            for attrib in tree.xpath("/rss/channel/item/description"):
                description.append(attrib.text)

            for attrib in tree.xpath("/rss/channel/item/pubDate"):
                pubDate.append(attrib.text)

            for i in range(0, len(title) - 1):
                item = PyRSS2Gen.RSSItem(
                    title=title[i],
                    link=link[i],
                    description=description[i],
                    pubDate=pubDate[i]
                )
                rss.items.insert(0, item)

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
    file = open(destination, "w+")
    rss.write_xml(file)
    file.close()
