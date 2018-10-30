import PyRSS2Gen
import datetime
import json
from pathlib import Path
from lxml import etree


FIELDS_UNAVAILABLE = ["date_from", "date_until", "image"]
CONFIG_FIELDS = ["feed_title", "feed_description", "feed_url", "local_feed_url"]
rss = None


def create_initial_feed(feed_url, feed_title="Superform's RSS feed", feed_description="The RSS feed of Superform"):

    global rss
    rss = PyRSS2Gen.RSS2(
        title=feed_title,
        link=feed_url,
        description=feed_description,
        items=[]
    )

    return rss


def run(publishing, channel_config):
    global rss

    json_data = json.loads(channel_config)
    rss_local_file = json_data["local_feed_url"]
    rss_local_file_path = "./superform/plugins/rssfeeds/" + rss_local_file
    rss_url = json_data["feed_url"]
    rss_title = json_data["feed_title"]
    rss_description = json_data["feed_description"]

    file = Path(rss_local_file_path)

    if not file.exists():
        rss = create_initial_feed(feed_url=rss_url, feed_title=rss_title, feed_description=rss_description)
    else:
        tree = etree.parse(rss_local_file_path)

        if rss is None:
            rss = create_initial_feed(feed_url=rss_url, feed_title=rss_title, feed_description=rss_description)

            title = list()
            link = list()
            description = list()
            pub_date = list()

            for attrib in tree.xpath("/rss/channel/item/title"):
                title.append(attrib.text)

            for attrib in tree.xpath("/rss/channel/item/link"):
                link.append(attrib.text)

            for attrib in tree.xpath("/rss/channel/item/description"):
                description.append(attrib.text)

            for attrib in tree.xpath("/rss/channel/item/pubDate"):
                pub_date.append(datetime.datetime.strptime(attrib.text, "%a, %d %b %Y %X GMT"))

            for i in range(0, len(title)):
                item = PyRSS2Gen.RSSItem(
                    title=title[i],
                    link=link[i],
                    description=description[i],
                    pubDate=pub_date[i]
                )
                rss.items.append(item)

    pub_date = datetime.datetime.now()

    item = PyRSS2Gen.RSSItem(
                title=publishing.title,
                link=publishing.link_url,
                description=publishing.description,
                pubDate=pub_date)

    rss.items.insert(0, item)
    for post in rss.items:
        if post.pubDate + datetime.timedelta(365) < pub_date:
            rss.items.remove(post)
    with open(rss_local_file_path, "w+") as file:
        rss.write_xml(file)
