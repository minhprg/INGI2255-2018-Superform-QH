from flask import Blueprint, url_for, request, redirect, render_template

from superform import channels
from superform.models import db, Publishing, Channel
from superform.utils import login_required, datetime_converter, str_converter

pub_page = Blueprint('publishings', __name__)


@pub_page.route('/edit/<int:id>/<string:idc>/abort_edit_publishing', methods=["POST"])
@login_required()
def abort_edit_publishing(id, idc):
    return redirect(url_for('index'))


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


@pub_page.route('/edit/<int:id>/<string:idc>', methods=["GET"])
@login_required()
def edit_publishing(id, idc):
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()

    # Only publishing that have yet to be moderated can be viewed
    # TODO create a page to crearly indicate the error
    if pub.state != 3:
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
            return render_template('moderate_post.html', pub=pub, conf=False, validate_url='publishings.validate_edit_publishing', refuse_url='publishings.abort_edit_publishing', action='Edit')
        else:
            return render_template('moderate_post.html', pub=pub, conf=True, validate_url='publishings.validate_edit_publishing', refuse_url='publishings.abort_edit_publishing', action='Edit')


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
            return render_template('moderate_post.html', pub=pub, conf=False, validate_url='publishings.validate_publishing', refuse_url='publishings.refuse_publishing', action='Moderate')
        else:
            return render_template('moderate_post.html', pub=pub, conf=True, validate_url='publishings.validate_publishing', refuse_url='publishings.refuse_publishing', action='Moderate')


@pub_page.route('/moderate/<int:id>/<string:idc>/refuse_publishing', methods=["POST"])
@login_required()
def refuse_publishing(id, idc):
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()

    # Only publishings that have yet to be moderated can be refused.
    # TODO print an alert at top of page to indicate the problem
    if pub.state == 0:
        pub.state = 3
        db.session.commit()

    return redirect(url_for('index'))


def update_db(pub, state, plugin, c_conf):
    pub.date_from = str_converter(pub.date_from)
    pub.date_until = str_converter(pub.date_until)
    if request.method == "POST":
        pub.title = request.form.get('titlepost')
        pub.description = request.form.get('descrpost')
        pub.link_url = request.form.get('linkurlpost')
        pub.image_url = request.form.get('imagepost')
        pub.date_from = datetime_converter(request.form.get('datefrompost'))
        pub.date_until = datetime_converter(request.form.get('dateuntilpost'))

        pub.state = state
        db.session.commit()

        return True if channels.valid_conf(c_conf, plugin.CONFIG_FIELDS) else False


@pub_page.route('/moderate/<int:id>/<string:idc>/validate_publishing', methods=["POST"])
@login_required()
def validate_publishing(id, idc):
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()

    # Only pubs that have yet to be moderated can be accepted
    # TODO print an alert at top of page to indicate the problem
    if pub.state != 0:
        return redirect(url_for('index'))

    c = db.session.query(Channel).filter(Channel.id == pub.channel_id).first()
    plugin_name = c.module
    c_conf = c.config
    from importlib import import_module
    plugin = import_module(plugin_name)

    if not update_db(pub, 1, plugin, c_conf):
        return render_template('moderate_post.html', pub=pub, conf=True)

    plugin.run(pub, c_conf)

    return redirect(url_for('index'))


@pub_page.route('/edit/<int:id>/<string:idc>/validate_edit_publishing', methods=["POST"])
@login_required()
def validate_edit_publishing(id, idc):
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()

    # Only pubs that have yet to be moderated can be accepted
    # TODO print an alert at top of page to indicate the problem
    if pub.state != 3:
        return redirect(url_for('index'))

    c = db.session.query(Channel).filter(Channel.id == pub.channel_id).first()
    plugin_name = c.module
    c_conf = c.config
    from importlib import import_module
    plugin = import_module(plugin_name)

    if not update_db(pub, 0, plugin, c_conf):
        return render_template('moderate_post.html', pub=pub, conf=True, validate_url='publishings.validate_edit_publishing', refuse_url='publishings.abort_edit_publishing', action='Edit')

    return redirect(url_for('index'))
