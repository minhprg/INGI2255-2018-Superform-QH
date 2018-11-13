from flask import Blueprint, current_app, url_for, request, make_response, redirect, session, render_template

import requests
import json

from superform.utils import login_required, get_instance_from_module_path, get_modules_names, get_module_full_name
from superform.models import db, Channel
import ast

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


@channels_page.route("/callback_In", methods=['GET', 'POST'])
@login_required(admin_required=True)
def callback_In():
    """Page where LinkedIn returns the code to get the access token.
            Generate the access token from the code and save it to the DB."""
    app_key=current_app.config["LINKEDIN_API_KEY"]
    app_secret=current_app.config["LINKEDIN_API_SECRET"]
    code = request.args.get('code')
    state=request.args.get('state')
    if "error" in request.args:
        error = request.args.get('error')
        print(error)
    if(state!="9876543210"):
        print("boom")
        return 0
    canvas_url = url_for('channels.callback_In', _external=True)
    response = requests.post("https://www.linkedin.com/oauth/v2/accessToken",
                             data={"grant_type": "authorization_code", "code": code, "redirect_uri": canvas_url,
                                   "client_id": app_key, "client_secret": app_secret})
    response=response.json()
    token=response['access_token']
    headers= {'Authorization': 'Bearer '+token,'Host':'api.linkedin.com','Connection':'Keep-Alive','x-li-format': 'json',"Content-Type":"application/json"}
    data={"comment": "Check out developer.linkedin.com!","content": {"title": "LinkedIn Developers Resources","description": "Leverage LinkedIn's APIs to maximize engagement","submitted-url": "https://developer.linkedin.com","submitted-image-url": "https://www.catizz.com/medias/common/miaulement%20chat%20.jpg"},"visibility": {"code": "anyone"}}

    data=json.dumps(data)

    #response = requests.post("https://api.linkedin.com/v1/people/~/shares/?format=json",headers=headers,data=data)
    response = requests.post("https://api.linkedin.com/v1/companies/12654611/shares/?format=json",headers=headers,data=data)
    return 0

@channels_page.route("/test", methods=['GET', 'POST'])
@login_required(admin_required=True)
def linkedInAuth():
    """Page where LinkedIn is called to get the code to have the access token."""

    app_key = current_app.config["LINKEDIN_API_KEY"]
    result = createRequestCodeLinkedIn(app_key,"9876543210")
    return redirect(result)

def createRequestCodeLinkedIn(app_key,state):
    canvas_url = url_for('channels.callback_In', _external=True)
    returnUrl = "https://www.linkedin.com/uas/oauth2/authorization?response_type=code&scope=rw_company_admin&client_id="+app_key+"&state="+state+"&redirect_uri="+canvas_url
    return returnUrl
