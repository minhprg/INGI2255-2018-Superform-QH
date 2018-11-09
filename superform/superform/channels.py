from flask import Blueprint, current_app, url_for, request, make_response, redirect, session, render_template
from linkedin_v2 import linkedin

from superform.utils import login_required, get_instance_from_module_path, get_modules_names, get_module_full_name
from superform.models import db, Channel
import ast
import facebook

channels_page = Blueprint('channels', __name__)


@channels_page.route("/channels", methods=['GET', 'POST'])
@login_required(admin_required=True)
def channel_list():
    if request.method == "POST":
        action = request.form.get('@action', '')
        if action == "new":
            name = request.form.get('name')
            module = request.form.get('module')
            if module in get_modules_names(current_app.config["PLUGINS"].keys()):
                channel = Channel(name=name, module=get_module_full_name(module), config="{}")
                db.session.add(channel)
                db.session.commit()
        elif action == "delete":
            channel_id = request.form.get("id")
            channel = Channel.query.get(channel_id)
            if channel:
                db.session.delete(channel)
                db.session.commit()
        elif action == "edit":
            channel_id = request.form.get("id")
            channel = Channel.query.get(channel_id)
            name = request.form.get('name')
            channel.name = name
            db.session.commit()

    channels = Channel.query.all()
    return render_template("channels.html", channels=channels,
                           modules=get_modules_names(current_app.config["PLUGINS"].keys()))


@channels_page.route("/configure/<int:id>", methods=['GET', 'POST'])
@login_required(admin_required=True)
def configure_channel(id):
    c = Channel.query.get(id)
    m = c.module
    clas = get_instance_from_module_path(m)
    config_fields = clas.CONFIG_FIELDS

    if request.method == 'GET':
        if (c.config is not ""):
            d = ast.literal_eval(c.config)
            setattr(c, "config_dict", d)
        if m == 'superform.plugins.facebook':
            return render_template("channel_configure_facebook.html", channel=c, config_fields=config_fields,
                                   url_token=clas.get_url_for_token(id),
                                   pages=clas.get_list_user_pages(c.config_dict.get("access_token")))
        else:
            return render_template("channel_configure.html", channel=c, config_fields=config_fields)
    str_conf = "{"
    cfield = 0
    if m == 'superform.plugins.facebook':
        str_conf += "\"access_token\" : \"" + request.form.get("access_token") + "\""
        str_conf += ",\"page\" : \"" + request.form.get("page") + "\""
    else:
        for field in config_fields:
            if cfield > 0:
                str_conf += ","
            str_conf += "\"" + field + "\" : \"" + request.form.get(field) + "\""
            cfield += 1
    str_conf += "}"
    c.config = str_conf
    db.session.commit()
    return redirect(url_for('channels.channel_list'))


@channels_page.route("/callback_fb", methods=['GET', 'POST'])
@login_required(admin_required=True)
def callback_fb():
    """Page where Facebook returns the code to get the access token.
        Generate the access token from the code and save it to the DB."""
    id_channel = request.args.get('state')
    code = request.args.get('code')
    if id_channel is None:
        return redirect(url_for("channels.channel_list"))

    app_id = current_app.config["FACEBOOK_APP_ID"]
    app_secret = current_app.config["FACEBOOK_APP_SECRET"]
    canvas_url = url_for('channels.callback_fb', _external=True)
    graph = facebook.GraphAPI()
    try:
        res = graph.get_access_token_from_code(code, canvas_url, app_id, app_secret)
        access_token = res['access_token']
    except facebook.GraphAPIError:
        access_token = 'Unable to generate access_token'

    channel = Channel.query.get(id_channel)
    # reset config and add new access_token
    channel.config = "{\"access_token\": \"" + str(access_token) + "\"}"

    db.session.commit()
    return redirect(url_for("channels.configure_channel", id=id_channel))

@channels_page.route("/callback_In", methods=['GET', 'POST'])
@login_required(admin_required=True)
def callback_In():
    """Page where LinkedIn returns the code to get the access token.
            Generate the access token from the code and save it to the DB."""
    app_key = current_app.config["LINKEDIN_API_KEY"]
    app_secret = current_app.config["LINKEDIN_API_SECRET"]
    canvas_url = url_for('channels.callback_In', _external=True)
    authentication = linkedin.LinkedInAuthentication(app_key, app_secret, canvas_url)
    application = linkedin.LinkedInApplication(authentication)
    print(request.args.get('code'))
    authentication.authorization_code = request.args.get('code')
    token = authentication.get_access_token()
    application = linkedin.LinkedInApplication(token=token)
    print(token)
    return 0

@channels_page.route("/test", methods=['GET', 'POST'])
@login_required(admin_required=True)
def linkedInAuth():
    """Page where LinkedIn is called to get the code to have the access token."""

    app_key = current_app.config["LINKEDIN_API_KEY"]
    app_secret = current_app.config["LINKEDIN_API_SECRET"]
    canvas_url = url_for('channels.callback_In', _external=True)
    authentication = linkedin.LinkedInAuthentication(app_key, app_secret, canvas_url)
    return redirect(authentication.authorization_url)