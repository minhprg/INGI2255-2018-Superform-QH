
from flask import url_for, current_app, Blueprint, request, redirect
from superform.utils import login_required
from superform.models import db, Channel
import requests
import json

linkedin_page = Blueprint('_linkedin_callback', __name__)

@linkedin_page.route("/callback_In", methods=['GET', 'POST'])
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
        return 0
    canvas_url = url_for('channels.callback_In', _external=True)
    response = requests.post("https://www.linkedin.com/oauth/v2/accessToken",
                             data={"grant_type": "authorization_code", "code": code, "redirect_uri": canvas_url,
                                   "client_id": app_key, "client_secret": app_secret})
    response=response.json()
    token=response['access_token']

    return 0