import os

import PyRSS2Gen
import datetime
import json
from pathlib import Path
from lxml import etree


FIELDS_UNAVAILABLE = ["date_from", "date_until", "image"]
CONFIG_FIELDS = ["feed_title", "feed_description", "feed_url", "local_feed_url"]
rss_feeds = {}


def create_initial_feed(feed_url, feed_title="Superform's RSS feed", feed_description="The RSS feed of Superform"):

    global rss_feeds
    rss_feeds = PyRSS2Gen.RSS2(
        title=feed_title,
        link=feed_url,
        description=feed_description,
        items=[]
    )

    return rss_feeds


def run(publishing, channel_config):
    global rss_feeds

    json_data = json.loads(channel_config)
    rss_feeds_url = json_data["feed_url"]
    rss_feeds_title = json_data["feed_title"]
    rss_feeds_description = json_data["feed_description"]
    rss_feeds_local_file = json_data["local_feed_url"]
    rss_plugin_path = os.path.dirname(__file__)
    rss_feeds_local_file_path = rss_plugin_path + "/rssfeeds/" + rss_feeds_local_file

    file = Path(rss_feeds_local_file_path)

    if not file.exists():
        rss_feeds = create_initial_feed(feed_url=rss_feeds_url, feed_title=rss_feeds_title, feed_description=rss_feeds_description)
    else:
        tree = etree.parse(rss_feeds_local_file_path)

        if rss_feeds is None:
            rss_feeds = create_initial_feed(feed_url=rss_feeds_url, feed_title=rss_feeds_title, feed_description=rss_feeds_description)

            title = list()
            link = list()
            description = list()
            pub_date = list()

            for attrib in tree.xpath("/rss_feeds/channel/item/title"):
                title.append(attrib.text)

            for attrib in tree.xpath("/rss_feeds/channel/item/link"):
                link.append(attrib.text)

            for attrib in tree.xpath("/rss_feeds/channel/item/description"):
                description.append(attrib.text)

            for attrib in tree.xpath("/rss_feeds/channel/item/pubDate"):
                pub_date.append(datetime.datetime.strptime(attrib.text, "%a, %d %b %Y %X GMT"))

            for i in range(0, len(title)):
                item = PyRSS2Gen.RSSItem(
                    title=title[i],
                    link=link[i],
                    description=description[i],
                    pubDate=pub_date[i]
                )
                rss_feeds.items.append(item)

    pub_date = datetime.datetime.now()

    item = PyRSS2Gen.RSSItem(
                title=publishing.title,
                link=publishing.link_url,
                description=publishing.description,
                pubDate=pub_date)

    rss_feeds.items.insert(0, item)
    for post in rss_feeds.items:
        if post.pubDate + datetime.timedelta(365) < pub_date:
            rss_feeds.items.remove(post)
    with open(rss_feeds_local_file_path, "w+") as file:
        rss_feeds.write_xml(file)
