import datetime

from flask import Blueprint, request, redirect, url_for, render_template

from superform import channels
from superform.models import db, Moderation, Post, Channel, User, Publishing, State
from superform.utils import str_converter, datetime_converter, time_converter, login_required, str_time_converter, \
    StatusCode

val_page = Blueprint('non-validation', __name__)


def commit_pub(pub, state):
    pub.date_from = str_converter(pub.date_from)
    pub.date_until = str_converter(pub.date_until)
    pub.title = request.form.get('titlepost')
    pub.description = request.form.get('descrpost')
    pub.link_url = request.form.get('linkurlpost')
    pub.image_url = request.form.get('imagepost')

    pub.date_from = datetime_converter(request.form.get('datefrompost'))
    time_from = time_converter(request.form.get('timefrompost')) if request.form.get('timefrompost') is not None else time_converter("0:0")
    pub.date_from = pub.date_from.replace(hour=time_from.hour, minute=time_from.minute)

    pub.date_until = datetime_converter(request.form.get('dateuntilpost'))
    time_until = time_converter(request.form.get('timeuntilpost')) if request.form.get('timeuntilpost') is not None else time_converter("0:0")
    pub.date_until = pub.date_until.replace(hour=time_until.hour, minute=time_until.minute)

    pub.state = state


def create_a_moderation(form, id, idc):
    message = form.get('commentpub') if form.get('commentpub') is not None else ""
    post = db.session.query(Post).filter(Post.id == id).first()
    mod = Moderation(user_id=post.user_id, post_id=id, channel_id=int(idc), message=message)

    db.session.add(mod)
    db.session.commit()


def get_moderation(pub):
    pub.date_until = pub.date_until if type(pub.date_until) == datetime.datetime else datetime_converter(pub.date_until)
    pub.date_from = pub.date_from if type(pub.date_from) == datetime.datetime else datetime_converter(pub.date_from)
    post = db.session.query(Post).filter(Post.id == pub.post_id).first()
    mod = [mod for _, _, _, mod in
           (db.session.query(Post, Channel, User, Moderation)
            .filter(Moderation.post_id == pub.post_id)
            .filter(Moderation.channel_id == pub.channel_id)
            .filter(Moderation.user_id == post.user_id))]
    return mod


@val_page.route('/moderate/<int:id>/<string:idc>/refuse_publishing', methods=["POST"])
@login_required()
def refuse_publishing(id, idc):
    """
    Refuse a publishing. The publishing is sent back to the author with the specified comment.
    Note that the changes the moderator may have done on the publishing itself will be lost.
    """
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()

    if pub.state != State.NOTVALIDATED.value:
        return redirect(url_for('index', messages="This publication has already been moderated"))

    if request.form.get('commentpub') == "":
        chan = db.session.query(Channel).filter(Channel.id == pub.channel_id).first()
        time_until = str_time_converter(pub.date_until)
        time_from = str_time_converter(pub.date_from)
        pub.date_from = str_converter(pub.date_from)
        pub.date_until = str_converter(pub.date_until)
        return render_template('moderate_publishing.html', pub=pub, time_from=time_from, time_until=time_until,
                               error_message="You must give a feedback to the author", chan=chan)

    mod = get_moderation(pub)

    if len(mod) == 0:
        create_a_moderation(request.form, id, idc)
    else:
        mod[0].message = request.form.get('commentpub')
        db.session.commit()

    # Only publishings that have yet to be moderated can be refused.
    if pub.state == State.NOTVALIDATED.value:
        pub.state = State.REFUSED.value
        db.session.commit()

    return redirect(url_for('index'))


@val_page.route('/moderate/<int:id>/<string:idc>/validate_publishing', methods=["POST"])
@login_required()
def validate_publishing(id, idc):
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()
    if pub.state != State.NOTVALIDATED.value:
        return redirect(url_for('index', messages="This publication has already been moderated"))

    c = db.session.query(Channel).filter(Channel.id == pub.channel_id).first()
    plugin_name = c.module
    c_conf = c.config
    from importlib import import_module
    plugin = import_module(plugin_name)

    error_msg = channels.check_config_and_validity(plugin, c_conf)
    if error_msg is not None:
        time_until = str_time_converter(pub.date_until)
        time_from = str_time_converter(pub.date_from)
        pub.date_from = str_converter(pub.date_from)
        pub.date_until = str_converter(pub.date_until)
        return render_template('moderate_publishing.html', pub=pub, chan=c,
                               error_message=error_msg, time_until=time_until, time_from=time_from)

    commit_pub(pub, State.VALIDATED.value)
    plug = plugin.run(pub, c_conf)

    if plug == StatusCode.ERROR.value:
        time_until = str_time_converter(pub.date_until)
        time_from = str_time_converter(pub.date_from)
        pub.date_from = str_converter(pub.date_from)
        pub.date_until = str_converter(pub.date_until)
        return render_template('moderate_publishing.html', pub=pub, time_from=time_from, time_until=time_until,
                               error_message='You need to enter at least a title or a description', chan=c)

    db.session.commit()

    #pub.date_from = str_converter(pub.date_from)
    #pub.date_until = str_converter(pub.date_until)

    mod = get_moderation(pub)

    if len(mod) == 0:
        create_a_moderation(request.form, id, idc)
    else:
        mod[0].message = request.form.get('commentpub')
        db.session.commit()

    if not plug:
        return redirect(url_for('index'))
    else:
        return plug


@val_page.route('/publishing/<int:id>/<string:idc>', methods=["GET"])
@login_required()
def view_publishing(id, idc):
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()
    c = db.session.query(Channel).filter(Channel.id == pub.channel_id).first()

    time_until = str_time_converter(pub.date_until)
    time_from = str_time_converter(pub.date_from)
    pub.date_until = str_converter(pub.date_until)
    pub.date_from = str_converter(pub.date_from)

    if request.method == "GET":
        return render_template('show_message.html', pub=pub, chan=c, time_until=time_until, time_from=time_from)


@val_page.route('/feedback/<int:id>/<string:idc>', methods=["GET"])
@login_required()
def view_feedback(id, idc):
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()

    c = db.session.query(Channel).filter(Channel.id == pub.channel_id).first()
    # Only publishing that have yet to be moderated can be viewed
    if pub.state == State.NOTVALIDATED.value:
        return redirect(url_for('index', messages='This publication has not yet been moderated'))

    mod = get_moderation(pub)
    if mod:
        message = mod[0].message
    else:
        message = ""

    time_until = str_time_converter(pub.date_until)
    time_from = str_time_converter(pub.date_from)
    pub.date_until = str_converter(pub.date_until)
    pub.date_from = str_converter(pub.date_from)

    if request.method == "GET":
        return render_template('show_message.html', pub=pub, mod=message, chan=c, time_from=time_from, time_until=time_until)


@val_page.route('/rework/<int:id>/<string:idc>/abort_edit_publishing', methods=["POST"])
@login_required()
def abort_rework_publishing(id, idc):
    return redirect(url_for('index'))


@val_page.route('/rework/<int:id>/<string:idc>', methods=["GET"])
@login_required()
def rework_publishing(id, idc):
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()
    c = db.session.query(Channel).filter(Channel.id == pub.channel_id).first()

    # Only refused publishings can be reworked
    # NOTE We could also allow unmoderated publishings to be reworked, but this overlaps the "editing" feature.
    if pub.state != State.REFUSED.value:
        return redirect(url_for('index'))

    mod = get_moderation(pub)
    if mod:
        message = mod[0].message
    else:
        message = ""

    time_until = str_time_converter(pub.date_until)
    time_from = str_time_converter(pub.date_from)
    pub.date_from = str_converter(pub.date_from)
    pub.date_until = str_converter(pub.date_until)

    if request.method == "GET":
        return render_template('rework_publishing.html', pub=pub, mod=message, chan=c, time_until=time_until, time_from=time_from)


@val_page.route('/rework/<int:id>/<string:idc>/validate_edit_publishing', methods=["POST"])
@login_required()
def validate_rework_publishing(id, idc):
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()
    post = db.session.query(Post).filter(Post.id == id).first()
    # Only pubs that have yet to be moderated can be accepted
    if pub.state == State.VALIDATED.value:
        return redirect(url_for('index', messages='This publication has already been reworked'))

    new_post = Post(user_id=post.user_id, title=post.title, description=post.description,
                    date_created=post.date_created, link_url=post.link_url, image_url=post.image_url,
                    date_from=post.date_from, date_until=post.date_until, source=post.source)
    db.session.add(new_post)
    db.session.commit()

    new_pub = Publishing(post_id=new_post.id, channel_id=pub.channel_id, state=pub.state, title=pub.title,
                         date_until=pub.date_until, date_from=pub.date_from)

    pub.state = State.OUTDATED.value
    db.session.add(new_pub)
    db.session.commit()

    commit_pub(new_pub, State.NOTVALIDATED.value)
    db.session.commit()
    return redirect(url_for('index'))
