import datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from superform import channels
from superform.models import db, Moderation, Post, Channel, User, Publishing, State
from superform.utils import str_converter, datetime_converter, time_converter, login_required, str_time_converter, \
    StatusCode

val_page = Blueprint('non-validation', __name__)


def update_pub(pub, state):
    """
    Update the publication with the new values in the form
    :param pub: the publication to update
    :param state: the new state of the publication
    """
    pub.date_from = str_converter(pub.date_from)
    pub.date_until = str_converter(pub.date_until)
    pub.title = request.form.get('titlepost')
    pub.description = request.form.get('descrpost')
    pub.link_url = request.form.get('linkurlpost')
    pub.image_url = request.form.get('imagepost')
    pub.rss_feed = request.form.get('linkrssfeedpost')

    pub.date_from = datetime_converter(request.form.get('datefrompost'))
    time_from = time_converter(request.form.get('timefrompost')) if request.form.get('timefrompost') is not None else time_converter("0:0")
    pub.date_from = pub.date_from.replace(hour=time_from.hour, minute=time_from.minute)

    pub.date_until = datetime_converter(request.form.get('dateuntilpost'))
    time_until = time_converter(request.form.get('timeuntilpost')) if request.form.get('timeuntilpost') is not None else time_converter("0:0")
    pub.date_until = pub.date_until.replace(hour=time_until.hour, minute=time_until.minute)

    pub.state = state


def create_a_moderation(form, id, idc, parent_post_id=None):
    """
    Create a new moderation and add it to the database
    :param form: the actual form
    :param id: post id
    :param idc: channel id
    :param parent_post_id: post id of the previous post (in case of a rework)
    """
    message = form.get('commentpub')

    if not parent_post_id:
        mod = Moderation(moderator_id=session.get("user_id", ""), post_id=id, channel_id=int(idc), message=message)
    else:
        mod = Moderation(moderator_id=None, post_id=id, channel_id=int(idc), message=message, parent_post_id=parent_post_id)

    db.session.add(mod)
    db.session.commit()


def get_moderation(pub):
    """
    get the moderations of the publishing
    :param pub: the publishing from whom we want to get the moderations
    :return: a list of moderations
    """
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
            parent_mod = db.session.query(Moderation).filter(Moderation.post_id == new_mod[0].parent_post_id).first()
            new_mod.insert(0, parent_mod)

    return new_mod


@val_page.route('/moderate/<int:id>/<string:idc>/refuse_publishing', methods=["POST"])
@login_required()
def refuse_publishing(id, idc):
    """
    Refuse a publishing. The publishing is sent back to the author with the specified comment.
    Note that the changes the moderator may have done on the publishing itself will be lost.
    :param id: post id
    :param idc: channel id
    """
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()

    if pub.state != State.NOTVALIDATED.value:
        flash("This publication has already been moderated", category='info')
        return redirect(url_for('index'))

    if request.form.get('commentpub') == "":
        flash("You must give a feedback to the author", category='error')
        return redirect(url_for('publishings.moderate_publishing', id=id, idc=idc))

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

    flash("The publishing has successfully been refused.", category='success')
    return redirect(url_for('index'))


@val_page.route('/moderate/<int:id>/<string:idc>/validate_publishing', methods=["POST"])
@login_required()
def validate_publishing(id, idc):
    """
    Validate a publishing, the changes made by the moderator will be saved and published. Create a new moderation for
    this publishing.
    :param id: post id
    :param idc: channel id
    :return: redirect to the index if everything went well else display an error message
    """
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()
    if pub.state != State.NOTVALIDATED.value:
        flash("This publication has already been moderated", category='info')
        return redirect(url_for('index'))

    c = db.session.query(Channel).filter(Channel.id == pub.channel_id).first()
    plugin_name = c.module
    c_conf = c.config
    from importlib import import_module
    plugin = import_module(plugin_name)

    error_msg = channels.check_config_and_validity(plugin, c_conf)
    if error_msg is not None:
        flash(error_msg, category='error')
        return redirect(url_for('publishings.moderate_publishing', id=id, idc=idc))

    update_pub(pub, State.VALIDATED.value)

    try:
        plug_exitcode = plugin.run(pub, c_conf)
    except Exception as e:
        flash("An error occurred while publishing, please contact an admin.", category='error')
        import sys
        print(str(e), file=sys.stderr)
        return redirect(url_for('publishings.moderate_publishing', id=id, idc=idc))

    if type(plug_exitcode) is tuple and len(plug_exitcode) >= 1 and plug_exitcode[0] == StatusCode.ERROR:
        flash(plug_exitcode[1], category='error')
        return redirect(url_for('publishings.moderate_publishing', id=id, idc=idc))

    if type(plug_exitcode) is tuple and len(plug_exitcode) >= 4 and plug_exitcode[0] == StatusCode.URL:
        return plug_exitcode[3]

    db.session.commit()

    mod = get_moderation(pub)

    if len(mod) == 0:
        create_a_moderation(request.form, id, idc)
    else:
        mod[-1].message = request.form.get('commentpub')
        mod[-1].moderator_id = session.get("user_id", "")
        db.session.commit()

    if type(plug_exitcode) is tuple and len(plug_exitcode) >= 2:
        message = plug_exitcode[1]
        if message:
            flash(message, category='success') # FIXME maybe rather in 'info' category?
        plug_exitcode = plug_exitcode[2]
    flash("The publishing has successfully been published.", category='success')
    if not plug_exitcode:
        return redirect(url_for('index'))
    else:
        return plug_exitcode


@val_page.route('/publishing/<int:id>/<string:idc>', methods=["GET"])
@login_required()
def view_publishing(id, idc):
    """
    View a publishing that has not yet been moderated with post_id = id and channel_id = idc
    :param id: post id
    :param idc: channel id
    :return: the actual publishing
    """
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
    """
    View the feedbacks and the publishing of a publishing that has already been moderated and accepted
    :param id: post id
    :param idc: channel id
    :return: the publishing with the feedbacks or an error message if the publishing hasn't yet been moderated
    """
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()

    c = db.session.query(Channel).filter(Channel.id == pub.channel_id).first()
    # Only publishing that have yet to be moderated can be viewed
    if pub.state == State.NOTVALIDATED.value:
        flash('This publication has not yet been moderated.', category='info')
        return redirect(url_for('index'))

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
    """
    Abort the rework of a publishing.
    :param id: post id
    :param idc: channel id
    :return: redirect to the index
    """
    flash("The rework has been aborted.", category='success')
    return redirect(url_for('index'))


@val_page.route('/rework/<int:id>/<string:idc>', methods=["GET"])
@login_required()
def rework_publishing(id, idc):
    """
    Rework a publishing that has been refused by a moderator
    :param id: post id
    :param idc: channel id
    :return: display an error message if the publishing hasn't been refused else render rework_publishing.html
    """
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()
    c = db.session.query(Channel).filter(Channel.id == pub.channel_id).first()

    # Only refused publishings can be reworked
    # NOTE We could also allow unmoderated publishings to be reworked, but this overlaps the "editing" feature.
    if pub.state != State.REFUSED.value:
        flash('This publication has not been refused and cannot be reworked.', category='info')
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
    """
    Validate the modifications applied to the publishing
    :param id: post id
    :param idc: channel id
    :return: an error message if the publishing has already been reworked else redirect to the index
    """
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()
    post = db.session.query(Post).filter(Post.id == id).first()
    # Only pubs that have yet to be moderated can be accepted
    if pub.state == State.VALIDATED.value:
        flash("This publication has already been reworked.", category='error')
        return redirect(url_for('index'))

    new_post = Post(user_id=post.user_id, title=pub.title, description=pub.description,
                    date_created=post.date_created, link_url=pub.link_url, image_url=pub.image_url,
                    date_from=pub.date_from, date_until=pub.date_until)
    db.session.add(new_post)
    db.session.commit()

    new_pub = Publishing(post_id=new_post.id, channel_id=pub.channel_id, state=pub.state, title=pub.title,
                         date_until=pub.date_until, date_from=pub.date_from, rss_feed=pub.rss_feed)

    pub.state = State.OUTDATED.value
    db.session.add(new_pub)
    db.session.commit()

    update_pub(new_pub, State.NOTVALIDATED.value)
    db.session.commit()

    create_a_moderation(request.form, new_post.id, new_pub.channel_id, parent_post_id=id)
    flash("The rework has been submitted.", category='success')
    return redirect(url_for('index'))
