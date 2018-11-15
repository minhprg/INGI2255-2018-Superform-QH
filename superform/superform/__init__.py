from flask import Flask, render_template, session, request
import pkgutil
import importlib

import superform.plugins
from superform.lists import lists_page
from superform.publishings import pub_page
from superform.models import db, Channel, Post, Publishing, User, State
from superform.authentication import authentication_page
from superform.authorizations import authorizations_page
from superform.channels import channels_page
from superform.posts import posts_page
from superform.rssfeed import feed_viewer_page
from superform.users import get_moderate_channels_for_user, is_moderator, channels_available_for_user

app = Flask(__name__)
app.config.from_json("config.json")

# Register blueprints
app.register_blueprint(authentication_page)
app.register_blueprint(authorizations_page)
app.register_blueprint(channels_page)
app.register_blueprint(posts_page)
app.register_blueprint(pub_page)
app.register_blueprint(lists_page)
app.register_blueprint(feed_viewer_page)

# Init dbs
db.init_app(app)

# List available channels in config
app.config["PLUGINS"] = {
    name: importlib.import_module(name)
    for finder, name, ispkg
    in pkgutil.iter_modules(superform.plugins.__path__, superform.plugins.__name__ + ".")
}


@app.route('/')
def index():
    user = User.query.get(session.get("user_id", "")) if session.get("logged_in", False) else None
    user_posts = []
    flattened_list_moderable_pubs = []
    my_accepted_pubs = []
    my_refused_pubs = []
    if user is not None:
        setattr(user, 'is_mod', is_moderator(user))
        from sqlalchemy import desc

        user_posts = db.session.query(Post).filter(Post.user_id == session.get("user_id", "")).order_by(desc(Post.id))\
            .limit(5).all()
        channels_moderable = get_moderate_channels_for_user(user)
        moderable_pubs_per_chan = (db.session.query(Publishing)
                                   .filter(Publishing.channel_id == c.id)
                                   .filter(Publishing.state == State.NOTVALIDATED.value)
                                   .order_by(desc(Publishing.post_id)).limit(5)
                                   .all() for c in channels_moderable)
        flattened_list_moderable_pubs = [y for x in moderable_pubs_per_chan for y in x]
        my_refused_pubs = [pub for _, _, pub in db.session.query(Channel, Post, Publishing)
                   .filter(Channel.id == Publishing.channel_id)
                   .filter(Publishing.post_id == Post.id)
                   .filter(Publishing.state == State.REFUSED.value)
                   .filter(Post.user_id == user.id).order_by(desc(Post.id)).limit(5).all()]
        my_accepted_pubs = [pub for _, _, pub in db.session.query(Channel, Post, Publishing)
            .filter(Channel.id == Publishing.channel_id)
            .filter(Publishing.post_id == Post.id)
            .filter(Publishing.state == State.VALIDATED.value)
            .filter(Post.user_id == user.id).order_by(desc(Post.id)).limit(5).all()]

    error_messages = ""
    if 'messages' in request.args:
        error_messages = request.args['messages']

    return render_template("index.html", user=user, posts=user_posts, publishings=flattened_list_moderable_pubs,
                           my_refused_publishings=my_refused_pubs, my_accepted_publishings=my_accepted_pubs,
                           error_message=error_messages, states=State)


@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403


@app.errorhandler(404)
def notfound(error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    # To use Flask over HTTPS we need to generate a certificate (cert.pem) and a key (key.pem)
    # and pass this option to Flask : --cert cert.pem --key key.pem
    app.run(ssl_context='adhoc')
