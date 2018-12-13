import datetime
import sys

from flask import Blueprint, request, redirect, url_for, render_template, session

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


def create_a_moderation(form, id, idc, parent_post_id=None):
    message = form.get('commentpub') if form.get('commentpub') is not None else ""

    if not parent_post_id:
        mod = Moderation(moderator_id=session.get("user_id", ""), post_id=id, channel_id=int(idc), message=message)
    else:
        mod = Moderation(moderator_id=None, post_id=id, channel_id=int(idc), message=message, parent_post_id=parent_post_id)

    db.session.add(mod)
    db.session.commit()


def get_moderation(pub):
    pub.date_until = pub.date_until if type(pub.date_until) == datetime.datetime else datetime_converter(pub.date_until)
    pub.date_from = pub.date_from if type(pub.date_from) == datetime.datetime else datetime_converter(pub.date_from)
    mod = [mod for _, _, _, mod in
           (db.session.query(Post, Channel, User, Moderation)
            .filter(Moderation.post_id == pub.post_id)
            .filter(Moderation.channel_id == pub.channel_id))]
    new_mod = list()
    if len(mod) > 0:
        new_mod.append(mod[0])
        while new_mod[0] and new_mod[0].parent_post_id:
            print(new_mod[0].parent_post_id, file=sys.stderr)
            parent_mod = db.session.query(Moderation).filter(Moderation.post_id == new_mod[0].parent_post_id).first()
            new_mod.insert(0, parent_mod)

    return new_mod


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
        mod[-1].message = request.form.get('commentpub')
        mod[-1].moderator_id = session.get("user_id", "")
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
        return render_template('moderate_publishing.html', pub=pub, chan=c, chan_not_conf=True,
                               error_message=error_msg, time_until=time_until, time_from=time_from)

    commit_pub(pub, State.VALIDATED.value)

    try:
        plug_exitcode = plugin.run(pub, c_conf)

        if type(plug_exitcode) is tuple and plug_exitcode[0] == StatusCode.ERROR:
            time_until = str_time_converter(pub.date_until)
            time_from = str_time_converter(pub.date_from)
            pub.date_from = str_converter(pub.date_from)
            pub.date_until = str_converter(pub.date_until)
            return render_template('moderate_publishing.html', pub=pub, time_from=time_from, time_until=time_until,
                                   error_message=plug_exitcode[1], chan=c)
    except:
        time_until = str_time_converter(pub.date_until)
        time_from = str_time_converter(pub.date_from)
        pub.date_from = str_converter(pub.date_from)
        pub.date_until = str_converter(pub.date_until)
        return render_template('moderate_publishing.html', pub=pub, chan=c, time_until=time_until, time_from=time_from,
                               error_message="An error occurred while publishing, please contact an admin.")

    db.session.commit()

    mod = get_moderation(pub)

    if len(mod) == 0:
        create_a_moderation(request.form, id, idc)
    else:
        mod[-1].message = request.form.get('commentpub')
        mod[-1].moderator_id = session.get("user_id", "")
        db.session.commit()

    if type(plug_exitcode) is tuple:
        plug_exitcode = plug_exitcode[2]
    if not plug_exitcode:
        return redirect(url_for('index'))
    else:
        return plug_exitcode


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

    time_until = str_time_converter(pub.date_until)
    time_from = str_time_converter(pub.date_from)
    pub.date_until = str_converter(pub.date_until)
    pub.date_from = str_converter(pub.date_from)

    if request.method == "GET":
        return render_template('show_message.html', pub=pub, mod=mod, chan=c, time_from=time_from, time_until=time_until)


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

    time_until = str_time_converter(pub.date_until)
    time_from = str_time_converter(pub.date_from)
    pub.date_from = str_converter(pub.date_from)
    pub.date_until = str_converter(pub.date_until)

    if request.method == "GET":
        return render_template('rework_publishing.html', pub=pub, mod=mod, chan=c, time_until=time_until, time_from=time_from)


@val_page.route('/rework/<int:id>/<string:idc>/validate_edit_publishing', methods=["POST"])
@login_required()
def validate_rework_publishing(id, idc):
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()
    post = db.session.query(Post).filter(Post.id == id).first()
    # Only pubs that have yet to be moderated can be accepted
    if pub.state == State.VALIDATED.value:
        return redirect(url_for('index', messages='This publication has already been reworked'))

    new_post = Post(user_id=post.user_id, title=pub.title, description=pub.description,
                    date_created=post.date_created, link_url=pub.link_url, image_url=pub.image_url,
                    date_from=pub.date_from, date_until=pub.date_until)
    db.session.add(new_post)
    db.session.commit()

    new_pub = Publishing(post_id=new_post.id, channel_id=pub.channel_id, state=pub.state, title=pub.title,
                         date_until=pub.date_until, date_from=pub.date_from)

    pub.state = State.OUTDATED.value
    db.session.add(new_pub)
    db.session.commit()

    commit_pub(new_pub, State.NOTVALIDATED.value)
    db.session.commit()

    create_a_moderation(request.form, new_post.id, new_pub.channel_id, parent_post_id=id)
    return redirect(url_for('index'))
