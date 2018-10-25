import json

from flask import Blueprint, current_app, url_for, request, make_response, redirect, session, render_template

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
                                   pages=clas.get_page(c.config_dict.get("access_token")))
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

    id_channel = request.args.get('state')
    code = request.args.get('code')

    app_id = "1672680826169132"
    canvas_url = "https://127.0.0.1:5000/callback_fb"
    graph = facebook.GraphAPI()
    res = graph.get_access_token_from_code(code, canvas_url, app_id, "152bd148cea3d9c7cacaa6cc234546ff")

    access_token = res['access_token']
    channel = Channel.query.get(id_channel)
    # reset config and add new access_token
    channel.config = "{\"access_token\": \"" + str(access_token) + "\"}"

    db.session.commit()
    return redirect(url_for("channels.configure_channel", id=id_channel))

