from flask import Flask, render_template, session, request
import pkgutil
import importlib

import superform.plugins
from superform.publishings import pub_page
from superform.models import db, User, Post,Publishing
from superform.authentication import authentication_page
from superform.authorizations import authorizations_page
from superform.channels import channels_page
from superform.posts import posts_page
from superform.rssfeed import feed_viewer_page
from superform.users import get_moderate_channels_for_user, is_moderator
from superform.plugins._linkedin_callback import linkedin_page
from superform.plugins._facebook_callback import facebook_page

app = Flask(__name__)
app.config.from_json("config.json")

# Register blueprints
app.register_blueprint(authentication_page)
app.register_blueprint(authorizations_page)
app.register_blueprint(channels_page)
app.register_blueprint(posts_page)
app.register_blueprint(pub_page)
app.register_blueprint(feed_viewer_page)
app.register_blueprint(facebook_page)
app.register_blueprint(linkedin_page)

# Init dbs
db.init_app(app)

# List available channels in config
app.config["PLUGINS"] = {}
for finder, name, ispkg in pkgutil.iter_modules(superform.plugins.__path__, superform.plugins.__name__ + "."):
    if name[18] != '_': # do not include files starting with an underscore (useful for callback pages)
        app.config["PLUGINS"][name] = importlib.import_module(name)


@app.route('/', methods=['GET', 'POST'])
def index():
    user = User.query.get(session.get("user_id", "")) if session.get("logged_in", False) else None
    posts=[]
    flattened_list_pubs =[]
    published_list=[]
    if user is not None:
        setattr(user,'is_mod',is_moderator(user))
        posts = db.session.query(Post).filter(Post.user_id == session.get("user_id", ""))
        chans = get_moderate_channels_for_user(user)
        pubs_per_chan = (db.session.query(Publishing).filter((Publishing.channel_id == c.id) &
                                                             (Publishing.state == 0)) for c in chans)
        published_per_chan = (db.session.query(Publishing).filter((Publishing.channel_id == c.id) &
                                                                  (Publishing.state == 1)) for c in chans)
        flattened_list_pubs = [y for x in pubs_per_chan for y in x]
        published_list = [y for x in published_per_chan for y in x]
        if request.method == "POST" and request.form.get('@action', '') == "delete":
            post_id = request.form.get("id")
            post = Post.query.get(post_id)
            if post:
                db.session.delete(post)
                db.session.commit()

    return render_template("index.html", user=user, posts=posts, publishings=flattened_list_pubs,
                           published=published_list)


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
