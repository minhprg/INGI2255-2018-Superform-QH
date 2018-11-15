import logging

from flask import Blueprint, redirect, render_template, request, url_for

from superform import channels
from superform.models import db, Publishing, Channel, Moderation, Post, User
from superform.utils import login_required, datetime_converter, str_converter

logging.basicConfig(level=logging.DEBUG)
pub_page = Blueprint('publishings', __name__)


def check_config_and_commit_pub(pub, state, plugin, c_conf):
    if channels.valid_conf(c_conf, plugin.CONFIG_FIELDS):
        pub.date_from = str_converter(pub.date_from)
        pub.date_until = str_converter(pub.date_until)
        pub.title = request.form.get('titlepost')
        pub.description = request.form.get('descrpost')
        pub.link_url = request.form.get('linkurlpost')
        pub.image_url = request.form.get('imagepost')
        pub.date_from = datetime_converter(request.form.get('datefrompost'))
        pub.date_until = datetime_converter(request.form.get('dateuntilpost'))

        pub.state = state
        db.session.commit()
    else:
        return False


def create_a_moderation(form, id, idc):
    message = form.get('commentpub') if form.get('commentpub') is not None else ""
    post = db.session.query(Post).filter(Post.id == id).first()
    mod = Moderation(user_id=post.user_id, post_id=id, channel_id=int(idc), message=message)

    db.session.add(mod)
    db.session.commit()


def create_a_publishing(post, chn, form):
    chan = str(chn.name)
    title_post = form.get(chan + '_titlepost') if (form.get(chan + '_titlepost') is not None) else post.title
    descr_post = form.get(chan + '_descriptionpost') if form.get(
        chan + '_descriptionpost') is not None else post.description
    link_post = form.get(chan + '_linkurlpost') if form.get(chan + '_linkurlpost') is not None else post.link_url
    image_post = form.get(chan + '_imagepost') if form.get(chan + '_imagepost') is not None else post.image_url
    date_from = datetime_converter(form.get(chan + '_datefrompost')) if datetime_converter(
        form.get(chan + '_datefrompost')) is not None else post.date_from
    date_until = datetime_converter(form.get(chan + '_dateuntilpost')) if datetime_converter(
        form.get(chan + '_dateuntilpost')) is not None else post.date_until
    pub = Publishing(post_id=post.id, channel_id=chn.id, state=0, title=title_post, description=descr_post,
                     link_url=link_post, image_url=image_post,
                     date_from=date_from, date_until=date_until)

    db.session.add(pub)
    db.session.commit()
    return pub


def get_moderation(pub):
    post = db.session.query(Post).filter(Post.id == pub.post_id).first()
    mod = [mod for _, _, _, mod in
           (db.session.query(Post, Channel, User, Moderation)
            .filter(Moderation.post_id == pub.post_id)
            .filter(Moderation.channel_id == pub.channel_id)
            .filter(Moderation.user_id == post.user_id))]
    return mod[0]


@pub_page.route('/moderate/<int:id>/<string:idc>', methods=["GET"])
@login_required()
def moderate_publishing(id, idc):
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()

    # Only publishing that have yet to be moderated can be viewed
    # TODO create a page to crearly indicate the error
    if pub.state != 0:
        return redirect(url_for('index'))

    c = db.session.query(Channel).filter(Channel.id == pub.channel_id).first()
    pub.date_from = str_converter(pub.date_from)
    pub.date_until = str_converter(pub.date_until)

    plugin_name = c.module
    c_conf = c.config
    from importlib import import_module
    plugin = import_module(plugin_name)

    if request.method == "GET":
        if channels.valid_conf(c_conf, plugin.CONFIG_FIELDS):
            return render_template('moderate_publishing.html', pub=pub, notconf=False)
        else:
            return render_template('moderate_publishing.html', pub=pub, notconf=True)


@pub_page.route('/moderate/<int:id>/<string:idc>/refuse_publishing', methods=["POST"])
@login_required()
def refuse_publishing(id, idc):
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()

    mod = get_moderation(pub)

    if len(mod) == 0:
        create_a_moderation(request.form, id, idc)
    else:  # FIXME: For the moment I'm updating the moderation, don't think it is the good thing to do
        mod[0].message = request.form.get('commentpub')
        db.session.commit()

    # Only publishings that have yet to be moderated can be refused.
    # TODO print an alert at top of page to indicate the problem
    if pub.state == 0:
        pub.state = 3
        db.session.commit()

    return redirect(url_for('index'))


@pub_page.route('/moderate/<int:id>/<string:idc>/validate_publishing', methods=["POST"])
@login_required()
def validate_publishing(id, idc):
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()

    mod = get_moderation(pub)

    if len(mod) == 0:
        create_a_moderation(request.form, id, idc)
    else:  # FIXME: Same as in refuse_publishing()
        mod[0].message = request.form.get('commentpub')
        db.session.commit()

    # Only pubs that have yet to be moderated can be accepted
    # TODO print an alert at top of page to indicate the problem
    if pub.state != 0:
        return redirect(url_for('index'))

    c = db.session.query(Channel).filter(Channel.id == pub.channel_id).first()
    plugin_name = c.module
    c_conf = c.config
    from importlib import import_module
    plugin = import_module(plugin_name)

    if check_config_and_commit_pub(pub, 1, plugin, c_conf):
        plugin.run(pub, c_conf)
        return redirect(url_for('index'))
    else:
        return render_template('moderate_publishing.html', pub=pub, notconf=True)


@pub_page.route('/feedback/<int:id>/<string:idc>', methods=["GET"])
@login_required()
def view_feedback(id, idc):
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()

    # Only publishing that have yet to be moderated can be viewed
    # TODO create a page to crearly indicate the error
    if pub.state == 0:
        return redirect(url_for('index'))

    mod = get_moderation(pub)

    if request.method == "GET":
        return render_template('show_message.html', pub=pub, mod=mod[0].message)


@pub_page.route('/edit/<int:id>/<string:idc>/abort_edit_publishing', methods=["POST"])
@login_required()
def abort_rework_publishing(id, idc):
    return redirect(url_for('index'))


@pub_page.route('/edit/<int:id>/<string:idc>', methods=["GET"])
@login_required()
def rework_publishing(id, idc):
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()

    # Only refused publishings can be reworked
    # NOTE We could also allow unmoderated publishings to be reworked, but this overlaps the "editing" feature.
    if pub.state != 3:
        return redirect(url_for('index'))

    mod = get_moderation(pub)

    if request.method == "GET":
        return render_template('rework_publishing.html', pub=pub, mod=mod.message)


@pub_page.route('/edit/<int:id>/<string:idc>/validate_edit_publishing', methods=["POST"])
@login_required()
def validate_rework_publishing(id, idc):
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()

    # Only pubs that have yet to be moderated can be accepted
    # TODO print an alert at top of page to indicate the problem
    if pub.state == 1:
        return redirect(url_for('index'))

    mod = get_moderation(pub)
    c = db.session.query(Channel).filter(Channel.id == pub.channel_id).first()
    plugin_name = c.module
    c_conf = c.config
    from importlib import import_module
    plugin = import_module(plugin_name)

    if check_config_and_commit_pub(pub, 0, plugin, c_conf):
        return redirect(url_for('index'))
    else:
        return render_template('rework_publishing.html', pub=pub, mod=mod)
