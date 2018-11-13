from flask import Blueprint, url_for, request, redirect, session, render_template

from superform.users import channels_available_for_user
from superform.utils import login_required, datetime_converter, str_converter, get_instance_from_module_path
from superform.models import db, Post, Publishing, Channel

import requests
from re import sub
from utils import build_ictv_server_request_args

posts_page = Blueprint('posts', __name__)
ictv_slides_templates = None


def create_a_post(form):
    user_id = session.get("user_id", "") if session.get("logged_in", False) else -1
    title_post = form.get('titlepost')
    descr_post = form.get('descriptionpost')
    link_post = form.get('linkurlpost')
    image_post = form.get('imagepost')
    date_from = datetime_converter(form.get('datefrompost'))
    date_until = datetime_converter(form.get('dateuntilpost'))
    p = Post(user_id=user_id, title=title_post, description=descr_post, link_url=link_post, image_url=image_post,
             date_from=date_from, date_until=date_until)
    db.session.add(p)
    db.session.commit()
    return p


def create_a_publishing(post, chn, form):

    chan = str(chn.name)
    if chn.module == 'superform.plugins.ictv':
        link_post = form.get(chan + '_ictv_url_type') + ':::' + post.link_url
        print(link_post)
    else:
        link_post = form.get(chan + '_linkurlpost') if form.get(chan + '_linkurlpost') is not None else post.link_url

    slide_typeform.get(chan + '_ictv_slide_type')

    title_post = form.get(chan + '_titlepost') if (form.get(chan + '_titlepost') is not None) else post.title
    descr_post = form.get(chan + '_descriptionpost') if form.get(
        chan + '_descriptionpost') is not None else post.description
    image_post = form.get(chan + '_imagepost') if form.get(chan + '_imagepost') is not None else post.image_url
    date_from = datetime_converter(form.get(chan + '_datefrompost')) if datetime_converter(
        form.get(chan + '_datefrompost')) is not None else post.date_from
    date_until = datetime_converter(form.get(chan + '_dateuntilpost')) if datetime_converter(
        form.get(chan + '_dateuntilpost')) is not None else post.date_until
    pub = Publishing(post_id=post.id, channel_id=chan, state=0, title=title_post, description=descr_post,
                     link_url=link_post, image_url=image_post,
                     date_from=date_from, date_until=date_until)

    db.session.add(pub)
    db.session.commit()
    return pub


@posts_page.route('/new', methods=['GET', 'POST'])
@login_required()
def new_post():
    global ictv_slides_templates
    user_id = session.get("user_id", "") if session.get("logged_in", False) else -1
    list_of_channels = channels_available_for_user(user_id)
    ictv_chan = None
    for elem in list_of_channels:
        m = elem.module
        if m == 'superform.plugins.ictv':
            ictv_chan = elem
        clas = get_instance_from_module_path(m)
        unaivalable_fields = ','.join(clas.FIELDS_UNAVAILABLE)
        setattr(elem, "unavailablefields", unaivalable_fields)

    if request.method == "GET":
        templates_request = None
        """ If there is ICTV in the list of channel, query the list of slides templates from the server """
        if ictv_chan is not None:
            request_args = build_ictv_server_request_args(ictv_chan.config, 'GET')
            # base_url = 'http://localhost:8000/channels/1/api/templates'
            # headers = {'accept': 'application/json', 'X-ICTV-editor-API-Key': 'azertyuiop'}
            # TODO : catch errors on request
            # TODO : check if API is enabled on ICTV and that API keys match
            ictv_slides_templates = requests.get(request_args['url'] + '/templates', headers=request_args['headers']).json()
            #templates_request = [sub('^template\-', '', i) for i in ictv_slides_templates]
            templates_request = {sub('^template\-', '', i):ictv_slides_templates[i] for i in ictv_slides_templates}
        return render_template('new.html', l_chan=list_of_channels, ictv_templates=templates_request)
    else:
        create_a_post(request.form)
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


@posts_page.route('/records')
@login_required()
def records():
    posts = db.session.query(Post).filter(Post.user_id == session.get("user_id", ""))
    records = [(p) for p in posts if p.is_a_record()]
    return render_template('records.html', records=records)
