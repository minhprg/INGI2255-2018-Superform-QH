from flask import session, render_template, Blueprint

from superform.users import is_moderator
from superform.models import User, db, Post, Publishing, Channel
from superform.utils import login_required

lists_page = Blueprint('lists', __name__)


def get_publications(user):
    setattr(user, 'is_mod', is_moderator(user))
    my_pubs = []
    if user is not None:
        my_pubs = [pub for _, _, pub in db.session.query(Channel, Post, Publishing)
            .filter(Channel.id == Publishing.channel_id)
            .filter(Publishing.post_id == Post.id)
            .filter(Post.user_id == user.id)]
    return my_pubs


@lists_page.route('/my_refused_publishings')
@login_required()
def refused_publishings():
    user = User.query.get(session.get("user_id", "")) if session.get("logged_in", False) else None
    return render_template("lists.html", title="Refused publishings",user=user, my_publishings=get_publications(user), state=3)


@lists_page.route('/my_accepted_publishings')
@login_required()
def accepted_publishings():
    user = User.query.get(session.get("user_id", "")) if session.get("logged_in", False) else None
    return render_template("lists.html", title="Accepted publishings", user=user, my_publishings=get_publications(user), state=1)


@lists_page.route('/my_unmoderated_publishings')
@login_required()
def unmoderated_publishings():
    user = User.query.get(session.get("user_id", "")) if session.get("logged_in", False) else None
    return render_template("lists.html", title="Unmoderated publishings", user=user, my_publishings=get_publications(user), state=0)


@lists_page.route('/unmoderated_publishings')
@login_required()
def moderator_unmoderated_publishings():
    user = User.query.get(session.get("user_id", "")) if session.get("logged_in", False) else None
    return render_template("lists.html", title="Unmoderated publishings", user=user, my_publishings=get_publications(user), state=0)
