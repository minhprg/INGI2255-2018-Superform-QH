import logging

from flask import Blueprint, flash, redirect, render_template, request, url_for

from superform import channels
from superform.models import db, Publishing, Channel, State
from superform.non_validation import get_moderation
from superform.utils import login_required, datetime_converter, time_converter, str_converter, str_time_converter

logging.basicConfig(level=logging.DEBUG)
pub_page = Blueprint('publishings', __name__)


def create_a_publishing(post, chn, form):
    chan = str(chn.name)

    plug_name = chn.module
    from importlib import import_module
    plug = import_module(plug_name)

    if 'forge_link_url' in dir(plug):
        link_post = plug.forge_link_url(chan, form)
    else:
        link_post = form.get(chan + '_linkurlpost') if form.get(chan + '_linkurlpost') is not None else post.link_url

    title_post = form.get(chan + '_titlepost') if (form.get(chan + '_titlepost') is not None) else post.title
    descr_post = form.get(chan + '_descriptionpost') if form.get(
        chan + '_descriptionpost') is not None else post.description
    rss_feed = form.get(chan + '_linkrssfeedpost')
    image_post = form.get(chan + '_imagepost') if form.get(chan + '_imagepost') is not None else post.image_url
    date_from = datetime_converter(form.get(chan + '_datefrompost')) if form.get(chan + '_datefrompost') is not None else post.date_from
    time_from = time_converter(form.get(chan + '_timefrompost')) if form.get(chan + '_timefrompost') is not None else None
    if date_from and time_from:
        date_from = date_from.replace(hour=time_from.hour, minute=time_from.minute)

    date_until = datetime_converter(form.get(chan + '_dateuntilpost')) if form.get(chan + '_dateuntilpost') is not None else post.date_until
    time_until = time_converter(form.get(chan + '_timeuntilpost')) if form.get(chan + '_timeuntilpost') is not None else None
    if date_until and time_until:
        date_until = date_until.replace(hour=time_until.hour, minute=time_until.minute)

    pub = Publishing(post_id=post.id, channel_id=chn.id, state=State.NOTVALIDATED.value, title=title_post, description=descr_post,
                     link_url=link_post, image_url=image_post,
                     date_from=date_from, date_until=date_until, rss_feed=rss_feed)

    db.session.add(pub)
    db.session.commit()
    return pub


def edit_a_publishing(post, chn, form):
    pub = db.session.query(Publishing).filter(Publishing.post_id == post.id).filter(Publishing.channel_id == chn.id).first() # ici ca renvoie None quand on modifie un publishing d'un channel qui n'existait pas encore: normal...
    if pub is None:
        return create_a_publishing(post,chn,form)
    else:
        chan = str(chn.name)
        pub.title = form.get(chan + '_titlepost') if (form.get(chan + '_titlepost') is not None) else post.title
        pub.description = form.get(chan + '_descriptionpost') if form.get(
            chan + '_descriptionpost') is not None else post.description
        pub.link_url = form.get(chan + '_linkurlpost') if form.get(chan + '_linkurlpost') is not None else post.link_url
        pub.image_url = form.get(chan + '_imagepost') if form.get(chan + '_imagepost') is not None else post.image_url
        pub.date_from = datetime_converter(form.get(chan + '_datefrompost')) if form.get(chan + '_datefrompost') is not None else post.date_from
        pub.date_until = datetime_converter(form.get(chan + '_dateuntilpost')) if form.get(chan + '_dateuntilpost') is not None else post.date_until
        pub.rss_feed = form.get(chan + '_linkrssfeedpost')
        db.session.commit()
        return pub


@pub_page.route('/moderate/<int:id>/<string:idc>', methods=["GET"])
@login_required()
def moderate_publishing(id, idc):
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()

    # Only publishing that have yet to be moderated can be viewed
    if pub.state != State.NOTVALIDATED.value:
        flash("This publication has already been moderated", category='info')
        return redirect(url_for('index'))

    c = db.session.query(Channel).filter(Channel.id == pub.channel_id).first()

    plugin_name = c.module
    c_conf = c.config
    from importlib import import_module
    plugin = import_module(plugin_name)

    mod = get_moderation(pub)
    if len(mod) > 0:
        mod.remove(mod[-1])

    time_until = str_time_converter(pub.date_until)
    time_from = str_time_converter(pub.date_from)
    pub.date_from = str_converter(pub.date_from)
    pub.date_until = str_converter(pub.date_until)

    if request.method == "GET":
        error_msg = channels.check_config_and_validity(plugin, c_conf)
        if error_msg is not None:
            flash(error_msg, category='error')
            chan_not_conf = True
        else:
            chan_not_conf = False
        return render_template('moderate_publishing.html', pub=pub, chan=c, mod=mod, chan_not_conf=chan_not_conf,
                               time_from=time_from, time_until=time_until)


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
    # FIXME ce n'est pas très propre d'utiliser un 'GET' pour une action qui mériterait un 'POST'
    # then treat the publish part
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc)
    pub.update({Publishing.state: State.PUBLISHED.value})
    db.session.commit()
    return redirect(url_for('index'))
