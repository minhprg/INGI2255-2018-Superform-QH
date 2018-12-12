import datetime
from flask import Blueprint, url_for, request, redirect, session, render_template

from superform.users import channels_available_for_user

from superform.models import db, Channel, Post, Publishing, State, User
from superform.publishings import create_a_publishing, edit_a_publishing
from superform.utils import login_required, datetime_converter, time_converter, str_converter, get_instance_from_module_path


posts_page = Blueprint('posts', __name__)


def create_a_post(form):
    user_id = session.get("user_id", "") if session.get("logged_in", False) else -1
    title_post = form.get('titlepost')
    descr_post = form.get('descriptionpost')
    link_post = form.get('linkurlpost')
    image_post = form.get('imagepost')
    rss_feed = form.get("linkrssfeedpost")

    date_from = datetime_converter(form.get('datefrompost'))

    date_until = datetime_converter(form.get('dateuntilpost'))

    p = Post(user_id=user_id, title=title_post, description=descr_post, link_url=link_post, image_url=image_post,
             date_from=date_from, date_until=date_until, rss_feed=rss_feed)
    db.session.add(p)
    db.session.commit()
    return p


def modify_a_post(form, post_id):
    post = db.session.query(Post).filter(Post.id == post_id).first()
    post.user_id = session.get("user_id", "") if session.get("logged_in", False) else -1
    post.title = form.get('titlepost')
    post.description = form.get('descriptionpost')
    post.link_url = form.get('linkurlpost')
    post.image_url = form.get('imagepost')
    post.date_from = datetime_converter(form.get('datefrompost'))
    post.date_until = datetime_converter(form.get('dateuntilpost'))
    db.session.commit()
    return post


@posts_page.route('/new', methods=['GET', 'POST'])
@login_required()
def new_post():
    user_id = session.get("user_id", "") if session.get("logged_in", False) else -1
    list_of_channels = channels_available_for_user(user_id)
    for elem in list_of_channels:
        m = elem.module
        clas = get_instance_from_module_path(m)
        unaivalable_fields = ','.join(clas.FIELDS_UNAVAILABLE)
        setattr(elem, "unavailablefields", unaivalable_fields)

    if request.method == "GET":
        return render_template('new.html', l_chan=list_of_channels,new=True)
    else:
        create_a_post(request.form)
    return redirect(url_for('index'))


@posts_page.route('/new/<int:post_id>', methods=['GET', 'POST'])
@login_required()
def copy_new_post(post_id):
    """
    This method copy the content of a post (defined by his post_id) and open the new post tab with all the informations
    of the original post copied in it (and with the title modified)
    :param post_id: id of the original post to be copied
    :return:
    """
    user_id = session.get("user_id", "") if session.get("logged_in", False) else -1
    list_of_channels = channels_available_for_user(user_id)
    for elem in list_of_channels:
        m = elem.module
        clas = get_instance_from_module_path(m)
        unavailable_fields = '.'.join(clas.FIELDS_UNAVAILABLE)
        setattr(elem, "unavailablefields", unavailable_fields)

    # Query the data from the original post
    original_post = db.session.query(Post).filter(Post.id == post_id).first()
    post = Post(user_id=user_id, title="Copy of " + original_post.title, description=original_post.description,
                link_url=original_post.link_url, image_url=original_post.image_url, date_from=original_post.date_from,
                date_until=original_post.date_until)
    if request.method == "GET":
        post.date_from = str_converter(post.date_from)
        post.date_until = str_converter(post.date_until)
        return render_template('new.html', l_chan=list_of_channels, post=post, new=True)
    else:
        create_a_post(request.form)
        return redirect(url_for('index'))


@posts_page.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required()
def edit_post(post_id):
    """
    This method allow the editing the content of a post (defined by his post_id) and opens the new post tab with all the information
    about the post in it
    :param post_id: id of the post to be edited
    :return:
    """
    user_id = session.get("user_id", "") if session.get("logged_in", False) else -1
    list_of_channels = channels_available_for_user(user_id)
    for elem in list_of_channels:
        m = elem.module
        clas = get_instance_from_module_path(m)
        unavailable_fields = '.'.join(clas.FIELDS_UNAVAILABLE)
        setattr(elem, "unavailablefields", unavailable_fields)

    # Query the data from the post
    post = db.session.query(Post).filter(Post.id == post_id).first()
    # Query the publishing of the post
    list_publishing = db.session.query(Publishing).filter(Publishing.post_id == post_id)

    # Get list of channels with publishing not yet publish or validated
    # and list of channels with not yet publishing
    list_chan_id_selected = []
    list_already_pub = []
    for pub in list_publishing:
        list_chan_id_selected.append(pub.channel_id)
        if pub.state == State.PUBLISHED.value or pub.state == State.VALIDATED.value:
            list_already_pub.append(pub.channel_id)
    list_chan_selected = []
    list_chan_not_selected = []
    for chan in list_of_channels:
        if list_chan_id_selected.__contains__(chan.id):
            if not list_already_pub.__contains__(chan.id):
                list_chan_selected.append(chan)
        else:
            list_chan_not_selected.append(chan)

    if request.method == "GET":
        post.date_from = str_converter(post.date_from)
        post.date_until = str_converter(post.date_until)
        return render_template('new.html', l_chan=list_chan_selected, post=post, new=False, l_chan_not=list_chan_not_selected)
    else:
        modify_a_post(request.form, post_id)
        return redirect(url_for('index'))


@posts_page.route('/publish/edit/<int:post_id>', methods=['POST'])
@login_required()
def publish_from_edit_post(post_id):
    # First edit the post
    p = modify_a_post(request.form,post_id)
    # Then treat the publish part
    if request.method == "POST":
        for elem in request.form:
            if elem.startswith("chan_option_"):
                def substr(elem):
                    import re
                    return re.sub('^chan\_option\_', '', elem)

                c = Channel.query.get(substr(elem))
                # for each selected channel options
                # edit the publication
                pub = edit_a_publishing(p, c, request.form)

    db.session.commit()
    return redirect(url_for('index'))


@posts_page.route('/publish', methods=['POST'])
@login_required()
def publish_from_new_post():
    # First create the post
    p = create_a_post(request.form)
    # then treat the publish part
    if request.method == "POST":
        for elem in request.form:
            if elem.startswith("chan_option_"):
                def substr(elem):
                    import re
                    return re.sub('^chan\_option\_', '', elem)

                c = Channel.query.get(substr(elem))
                # for each selected channel options
                # create the publication
                pub = create_a_publishing(p, c, request.form)

    db.session.commit()
    return redirect(url_for('index'))


@posts_page.route('/records', methods=["GET", "POST"])
@login_required()
def records():
    """
    This methods is called for the creation of the Records page
    """
    # FIXME Essayez de suivre le pattern PRG (post-redirect-get) pour éviter des misbehaviors
    # FIXME en cas de rechargement de la page
    # Check if there is any publishing to pass as archived
    publishings = db.session.query(Publishing).filter(Publishing.state == 1)\
        .filter(Publishing.date_until <= datetime.datetime.now())
    publishings.update({Publishing.state: 2})
    db.session.commit()

    # Check if a user is an admin
    admin = session.get("admin", False) if session.get("logged_in", False) else False

    # Check if a post has been send to delete an archive
    if request.method == "POST" and request.form.get('@action', '') == "delete":
        if admin:
            id = request.form.get("id")
            idc = request.form.get("idc")
            pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc)
            pub.delete()
            db.session.commit()
        else:
            # TODO, it seems like we have some cheater here
            pass

    user_id = session.get("user_id", "") if session.get("logged_in", False) else -1
    list_of_channels = channels_available_for_user(user_id)

    # Query all the archived publishings
    archives = db.session.query(Publishing).filter(Publishing.state == 2)

    # Take all archives and format the dates entries
    records = []
    for a in archives:
        allowed = False
        for channel in list_of_channels:
            if channel.name == a.channel_id:
                allowed = True
                break

        if allowed:
            date_from = str_converter(a.date_from)
            date_until = str_converter(a.date_until)
            records.append((a, date_from, date_until))

    return render_template('records.html', records=records, admin=admin)
