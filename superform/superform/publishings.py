import logging

from flask import Blueprint, redirect, render_template, request, url_for

from superform import channels
from superform.models import db, Publishing, Channel, State
from superform.utils import login_required, datetime_converter, time_converter, str_converter, str_time_converter

logging.basicConfig(level=logging.DEBUG)
pub_page = Blueprint('publishings', __name__)


def create_a_publishing(post, chn, form):
    chan = str(chn.name)
    title_post = form.get(chan + '_titlepost') if (form.get(chan + '_titlepost') is not None) else post.title
    descr_post = form.get(chan + '_descriptionpost') if form.get(
        chan + '_descriptionpost') is not None else post.description
    link_post = form.get(chan + '_linkurlpost') if form.get(chan + '_linkurlpost') is not None else post.link_url
    image_post = form.get(chan + '_imagepost') if form.get(chan + '_imagepost') is not None else post.image_url
    date_from = datetime_converter(form.get(chan + '_datefrompost')) if form.get(chan + '_datefrompost') is not None else post.date_from
    time_from = time_converter(form.get(chan + '_timefrompost')) if form.get(chan + '_timefrompost') is not None else None
    if date_from and time_from:
        date_from = date_from.replace(hour=time_from.hour, minute=time_from.minute)

    date_until = datetime_converter(form.get(chan + '_dateuntilpost')) if form.get(chan + '_dateuntilpost') is not None else post.date_until
    time_until = time_converter(form.get(chan + '_timeuntilpost')) if form.get(chan + '_timeuntilpost') is not None else None
    if date_until and time_until:
        date_until = date_until.replace(hour=time_until.hour, minute=time_until.minute)

    pub = Publishing(post_id=post.id, channel_id=chn.id, state=0, title=title_post, description=descr_post,
                     link_url=link_post, image_url=image_post,
                     date_from=date_from, date_until=date_until)

    db.session.add(pub)
    db.session.commit()
    return pub


@pub_page.route('/moderate/<int:id>/<string:idc>', methods=["GET"])
@login_required()
def moderate_publishing(id, idc):
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()

    # Only publishing that have yet to be moderated can be viewed
    if pub.state != State.NOTVALIDATED.value:
        return redirect(url_for('index', messages="This publication has already been moderated"))

    c = db.session.query(Channel).filter(Channel.id == pub.channel_id).first()

    plugin_name = c.module
    c_conf = c.config
    from importlib import import_module
    plugin = import_module(plugin_name)

    time_until = str_time_converter(pub.date_until)
    time_from = str_time_converter(pub.date_from)
    pub.date_from = str_converter(pub.date_from)
    pub.date_until = str_converter(pub.date_until)

    if request.method == "GET":
        error_msg = channels.check_config_and_validity(plugin, c_conf)
        if error_msg is None:
            return render_template('moderate_publishing.html', pub=pub, time_from=time_from,time_until=time_until)
        else:
            return render_template('moderate_publishing.html', pub=pub,
                                   error_message=error_msg, time_from=time_from,time_until=time_until)


@pub_page.route('/archive/<int:id>/<string:idc>', methods=["GET"])
@login_required()
def archive_publishing(id, idc):
    """
    This method is just a simple helper to quickly archive a publishing from the index page, it could be unnecessary to
    keep it later in the project development
    :param id: the id of the post
    :param idc: the id of the channel
    :return: redirect to the index page
    """
    # then treat the publish part
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc)
    pub.update({Publishing.state: 2})
    db.session.commit()
    return redirect(url_for('index'))
