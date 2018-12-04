from flask import session, render_template, Blueprint
from sqlalchemy import desc

from superform.users import is_moderator, get_moderate_channels_for_user
from superform.models import User, db, Post, Publishing, Channel, State
from superform.utils import login_required

lists_page = Blueprint('lists', __name__)


def get_publications(user):
    if user is None:
        return []
    setattr(user, 'is_mod', is_moderator(user))
    my_pubs = []
    if user is not None:
        my_pubs = [pub for _, _, pub in db.session.query(Channel, Post, Publishing)
            .filter(Channel.id == Publishing.channel_id)
            .filter(Publishing.post_id == Post.id)
            .filter(Post.user_id == user.id).order_by(desc(Publishing.post_id))]
    return my_pubs


def get_publications_to_moderate(user):
    channels_moderable = get_moderate_channels_for_user(user)
    moderable_pubs_per_chan = (db.session.query(Publishing)
                                   .filter(Publishing.channel_id == c.id)
                                   .filter(Publishing.state == State.NOTVALIDATED.value).order_by(desc(Publishing.post_id))
                                   .all() for c in channels_moderable)
    flattened_list_moderable_pubs = [y for x in moderable_pubs_per_chan for y in x]
    return flattened_list_moderable_pubs


@lists_page.route('/my_refused_publishings')
@login_required()
def refused_publishings():
    user = User.query.get(session.get("user_id", "")) if session.get("logged_in", False) else None
    return render_template("lists.html", title="Refused publishings",user=user, my_publishings=get_publications(user),
                           state=State.REFUSED.value, states=State)


@lists_page.route('/my_accepted_publishings')
@login_required()
def accepted_publishings():
    user = User.query.get(session.get("user_id", "")) if session.get("logged_in", False) else None
    return render_template("lists.html", title="Accepted publishings", user=user, my_publishings=get_publications(user),
                           state=State.VALIDATED.value, states=State)


@lists_page.route('/my_unmoderated_publishings')
@login_required()
def unmoderated_publishings():
    user = User.query.get(session.get("user_id", "")) if session.get("logged_in", False) else None
    return render_template("lists.html", title="Unmoderated publishings", user=user,
                           my_publishings=get_publications(user), state=State.NOTVALIDATED.value, states=State)


@lists_page.route('/unmoderated_publishings')
@login_required()
def moderator_unmoderated_publishings():
    user = User.query.get(session.get("user_id", "")) if session.get("logged_in", False) else None
    return render_template("lists.html", title="Unmoderated publishings", user=user,
                           my_publishings=get_publications_to_moderate(user), state=State.NOTVALIDATED.value,
                           to_moderate=True, states=State)
