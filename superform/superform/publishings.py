from flask import Blueprint, url_for, request, redirect, render_template, session

from superform.utils import login_required, datetime_converter, str_converter
from superform.models import db, Publishing, Channel

pub_page = Blueprint('publishings', __name__)


@pub_page.route('/moderate/<int:id>/<string:idc>', methods=["GET", "POST"])
@login_required()
def moderate_publishing(id, idc):
    pub = db.session.query(Publishing).filter(Publishing.post_id == id, Publishing.channel_id == idc).first()
    pub.date_from = str_converter(pub.date_from)
    pub.date_until = str_converter(pub.date_until)
    if request.method == "GET":
        return render_template('moderate_post.html', pub=pub)
    else:
        pub.title = request.form.get('titlepost')
        pub.description = request.form.get('descrpost')
        pub.link_url = request.form.get('linkurlpost')
        pub.image_url = request.form.get('imagepost')
        pub.date_from = datetime_converter(request.form.get('datefrompost'))
        pub.date_until = datetime_converter(request.form.get('dateuntilpost'))
        #state is shared & validated
        pub.state = 1
        db.session.commit()
        #running the plugin here
        c=db.session.query(Channel).filter(Channel.name == pub.channel_id).first()
        plugin_name = c.module
        c_conf = c.config
        from importlib import import_module
        plugin = import_module(plugin_name)
        plugin.run(pub, c_conf)

        return redirect(url_for('index'))


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


