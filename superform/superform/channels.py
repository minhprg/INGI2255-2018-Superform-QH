import json

from flask import Blueprint, current_app, url_for, request, make_response, redirect, session, render_template

import requests
import json

from superform.utils import login_required, get_instance_from_module_path, get_modules_names, get_module_full_name
from superform.models import db, Channel
import ast

channels_page = Blueprint('channels', __name__)


def check_config_and_validity(plugin, c_conf):
    '''Check the current config and validity of the channel'''
    config_json = json.loads(c_conf)
    for field in plugin.CONFIG_FIELDS:
        if field not in config_json:
            return "This channel has not yet been configured"
    try:
        test_channel_still_valid = plugin.check_validity(c_conf)
        if test_channel_still_valid != None:
            error_message = 'You can no longer publish on this channel for the moment. '
            error_message += test_channel_still_valid
            error_message += ' Please contact an administrator to fix this error.'
            return error_message

    except AttributeError:
        pass
    return None


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
        return redirect(url_for("channels.channel_list"))
    else:
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
        if c.config is not "":
            d = ast.literal_eval(c.config)
            setattr(c, "config_dict", d)
        try:
            return clas.render_specific_config_page(c, config_fields)
        except AttributeError:
            return render_template("channel_configure.html", channel=c, config_fields=config_fields)
    str_conf = "{"
    cfield = 0
    for field in config_fields:
        if cfield > 0:
            str_conf += ","
        str_conf += "\"" + field + "\" : \"" + request.form.get(field) + "\""
        cfield += 1
    str_conf += "}"
    c.config = str_conf
    db.session.commit()
    return redirect(url_for('channels.channel_list'))
