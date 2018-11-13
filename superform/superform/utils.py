from datetime import datetime
from functools import wraps
from flask import render_template, session, current_app
from requests import get
from re import sub


from superform.models import Authorization, Channel


def login_required(admin_required=False):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get("logged_in", False) or (admin_required and not session.get("admin", False)):
                return render_template("403.html"), 403
            else:
                return f(*args, **kwargs)
        return decorated_function
    return decorator


def datetime_converter(stri):
    return datetime.strptime(stri, "%Y-%m-%d")


def str_converter(datet):
    return datetime.strftime(datet,"%Y-%m-%d")


def get_instance_from_module_path(module_p):
    module_p=module_p.replace(".","/")
    import importlib.util
    spec = importlib.util.spec_from_file_location("module.name", module_p+".py")
    foo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(foo)
    return foo


def get_modules_names(modules_keys):
    return [m.split('.')[2] for m in modules_keys]


def get_module_full_name(module_name):
    for m in current_app.config["PLUGINS"].keys():
        if(m.split('.')[2] == module_name):
            return m


def build_ictv_server_request_args(channel_config, method):
    import json
    json_data = json.loads(channel_config)
    base_url = 'http://' + json_data['ictv_server_fqdn'] + '/channels/' + json_data['ictv_channel_id'] + '/api'
    headers = {'accept': 'application/json', 'X-ICTV-editor-API-Key': json_data['ictv_api_key']}
    if method == 'POST':
        headers['Content-Type'] = 'application/json'
    return {'url': base_url, 'headers': headers}


def get_ictv_templates(channel_config):
    request_args = build_ictv_server_request_args(channel_config, 'GET')
    # TODO : catch errors on request
    # TODO : check if API is enabled on ICTV and that API keys match
    ictv_slides_templates = get(request_args['url'] + '/templates', headers=request_args['headers']).json()
    return {sub('^template\-', '', i): ictv_slides_templates[i] for i in ictv_slides_templates if 'title-1' in ictv_slides_templates[i]}
