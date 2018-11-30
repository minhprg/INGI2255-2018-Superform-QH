import json
from requests import get, post, exceptions
import datetime

FIELDS_UNAVAILABLE = ['ictv_data_form']

CONFIG_FIELDS = ['ictv_server_fqdn', 'ictv_channel_id', 'ictv_api_key']


def generate_warning_popup(msg):
    return '<div class="alert alert-danger">\n \
            \t<strong>ERROR</strong>\n' + msg + '\n</div>\n'


class IctvException(Exception):
    msg = ''

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

    def popup(self):
        return generate_warning_popup(self.msg)


class IctvServerConnection(IctvException):
    # TODO : refactor the error messages
    def __init__(self, error_code, **kwargs):
        client_msg = ''
        if 'msg' in kwargs:
            client_msg = kwargs['msg']
        self.msg = '<p>Bad auhtentication : Superform cannot contact the ICTV server !</p>\n\n'
        if error_code == 403:
            self.msg += 'Please, check the following points :\n' \
                        '\t* Is the channel id given in the configuration the one from the ICTV server ?\n' \
                        '\t* Is the REST API enabled on the channel of the ICTV server ?\n' \
                        '\t* Are the API keys matching ?\n'
        elif error_code == 400:
            self.msg += '<p>The ' + client_msg + ' was misformed. Please correct the data and retry.</p>\n' \
                        '<p>If the error persists, take contact with an administrator.</p>'
        elif error_code == 404:
            if client_msg == 'slide':
                self.msg += '<p>The capsule for the slide was not found on the server.</p>'
            else:
                self.msg += '<p>The ictv server is unaccessible. The requests toward the server fails.</p>\n' \
                            '<p>Superform cannot ask the different slides layouts ...</p>'


class IctvChannelConfiguration(IctvException):
    def __init__(self, fields):
        self.msg = '<p>The following configuration fields of the <strong>' + fields[-1] + \
                   '</strong> channel are misconfigured : </p>\n\t<ul>'
        for i in fields[0:-1]:
            self.msg = self.msg + '\t<li>' + i + '</li>\n'

        self.msg = self.msg + '\t</ul>\n<p>You wont be able to submit your post on this channel !</p>\n<p>Please, ' \
                              'refer to the channel administrator.</p>\n'


class IctvWrongSlideType(IctvException):
    pass


# TODO : more interesting to have "plugins manager" in core application to check the configuration
def check_ictv_channel_config(chan_name, chan_config):
    """
    Check if the ictv channel is properly configured
    :param chan_name: the channel name having ictv as plugin
    :param chan_config:
    :raise: IctvChannelConfiguration if the channel is misconfigured
    """
    json_data = json.loads(chan_config)
    missing_fields = [i for i in CONFIG_FIELDS if (i not in json_data or json_data[i] == 'None')]
    if len(missing_fields) != 0:
        missing_fields.append(chan_name)
        raise IctvChannelConfiguration(missing_fields)
    else:
        return json_data


def build_ictv_server_request_args(chan_name, chan_config, method):
    """
    Return the headers required to communicate with the ICTV server given the channel configuration and the type of
    request
    :param channel: the channel having ictv as plugin
    :param method: the method of the HTTP request
    :return: a dict with the headers of the method of the HTTP request and the url of the channel of the ICTV server
    :raise: IctvChannelConfiguration if the channel is misconfigured
    """
    json_data = check_ictv_channel_config(chan_name, chan_config)

    base_url = 'http://' + json_data['ictv_server_fqdn'] + '/channels/' + json_data['ictv_channel_id'] + '/api'
    headers = {'accept': 'application/json', 'X-ICTV-editor-API-Key': json_data['ictv_api_key']}
    if method == 'POST':
        headers['Content-Type'] = 'application/json'
    return {'url': base_url, 'headers': headers}


def get_ictv_templates(chan_name, chan_config):
    """
    Request the dict of the different slides layout used by the ICTV server
    :param channel: the channel having ictv as plugin
    :return: the dict of the slides layout
    :raise: IctvChannelConfiguration if the channel is misconfigured
    :raise: IctvServerConnection if the server is not accessible or if the given configuration does not match any
    channels on the ICTV server
    """
    from re import sub

    """ Raise IctvChannelConfiguration if the channel is misconfigured """
    request_args = build_ictv_server_request_args(chan_name, chan_config, 'GET')
    try:
        response = get(request_args['url'] + '/templates', headers=request_args['headers'])
    except exceptions.ConnectionError as e:
        raise IctvServerConnection(404)

    """ Raise IctvServerConnection if the server replies with status code different from 200 """
    if response.status_code != 200:
        raise IctvServerConnection(response.status_code)

    ictv_slides_templates = response.json()
    if type(ictv_slides_templates) != dict:
        # TODO : check the dict format ?
        pass

    # TODO : add filter function to remove the unusable slides layouts ?

    return {sub('^template-', '', i): ictv_slides_templates[i] for i in ictv_slides_templates
            if 'title-1' in ictv_slides_templates[i]}


def forge_link_url(chan, form):
    from re import sub
    link_post = ''
    slide_type = form.get(chan + '_ictv_slide_type')
    if slide_type is not None:
        req = form.to_dict()
        for i in req:
            if chan + '_data_' + slide_type in i:
                a = sub('^' + chan + '_data_' + slide_type + '_', '', i)
                link_post = link_post + a + ":::" + req[i] + ','

        link_post = link_post + slide_type

    return link_post

def generate_ictv_dropdown_control(chan_name):

    code = '$("#' + chan_name + '_ictv_slide_choice_button").click(function () {' \
            'var name = $("#'+ chan_name + '_ictv_slide_choice_button input:radio:checked").val();\n' \
            '$(".' + chan_name + '_ictv_slide_choice").hide();\n' \
            '$("#' + chan_name + '_ictv_form_"+name).show();\n' \
            '});'
    return code


def generate_ictv_dropdown(chan_name, templates):
    button_id = chan_name + '_ictv_slide_choice_button'
    ret = '<div class="form-group chan_names" id="'+ button_id + '">\n<meta id="chan_name" data-chan_name="' + \
          chan_name + '">\n'
    ret = ret + '\t<button class="dropdown-toggle" type="button" data-toggle="dropdown" ' \
                '>Slide Layout<span class="caret"></span></button>\n'
    ret = ret + '\t<ul class="dropdown-menu">\n'
    for index, temp in enumerate(templates):
        input_id = chan_name + '_ictv_slide_type_' + temp
        input_name = chan_name + '_ictv_slide_type'
        ret = ret + '\t\t<li>\n\t\t\t<div class = "form-check">\n'
        ret = ret + '\t\t\t\t<input class="form-check-input" type="radio" name="' + input_name + \
                    '"id="' + input_id + '" value="' + temp + '" ' + ('checked' if index == 0 else '') + '>\n'
        ret = ret + '\t\t\t\t<label class="form-check-label" for="' + input_id + \
                    '">' + templates[temp]["description"] + '</label>\n\t\t\t</div>\n\t\t</li>\n'

    ret = ret + '\t</ul>\n</div>\n'

    return ret


def generate_ictv_data_form(chan_name, templates):
    ret = ''

    for index, temp in enumerate(templates):
        div_id = chan_name + '_ictv_form_' + temp
        ret = ret + '<div id="' + div_id + '" class=\"'+ chan_name +'_ictv_slide_choice\" ' + \
              ('style=\"display: none;\"' if index != 0 else '') + '>\n'
        ret = ret + '\t<h5>' + templates[temp]['name'] + '</h5>\n'

        for field in templates[temp]:
            if field != 'description' and field != 'name' and 'subtitle' not in field and 'title' not in field and \
                    'text' not in field:
                ret = ret + '\t<div class="form-group">\n'
                ret = ret + '\t\t<label for="' + chan_name + '_data_' + temp + '_' + field + \
                            '">' + field + '</label><br>\n'
                ret = ret + '\t\t<input type="text" name="' + chan_name + '_data_' + temp + '_' + field + \
                            '" id="' + chan_name + '_data_' + temp + '_' + field + '" class="form-control">\n'
                ret = ret + '\t</div>\n'

        ret = ret + '</div>\n'

    return ret


def generate_ictv_fields(chan_name, chan_config):
    templates = get_ictv_templates(chan_name, chan_config)
    # TODO : maybe avoid  the replication of the fields dict
    return {'dropdown': generate_ictv_dropdown(chan_name, templates),
            'data': generate_ictv_data_form(chan_name, templates),
            'control': generate_ictv_dropdown_control(chan_name),
            'error': ''}


def process_ictv_channels(channels):
    """
    Generate the fields to pass to the view form for each ictv channel
    :param channels: list of the ictv channels
    :return: the fields to pass to the view form
    """
    ret = {}
    for chan in channels:
        try:
            fields = generate_ictv_fields(chan.name, chan.config)
        except (IctvChannelConfiguration, IctvServerConnection) as e:
            # TODO : maybe avoid  the replication of the fields dict
            ret[chan.name] = {'data': '', 'dropdown': '', 'control': '', 'error': e.popup()}
        else:
            ret[chan.name] = fields

    return ret


def generate_slide(chan_conf, pub):
    """
    Request the ICTV server the different slides layout and generate the slide corresponding to the publication data
    :param chan_conf: the configuration of the ictv channel
    :param pub: the publication to turn into a slide
    :return: the JSON representation of the slide
    :raise IctvServerConnection: if the communication with the server is impossible for any reason
    :raise IctvChannelConfiguration: if the channel is misconfigured and that does not allow to contact the ICTV server
    :raise IctvWrongSlideType: if the slide type given with the publication does not exist on the ICTV server. Should
                                never be raised
    """
    splited_url = pub.link_url.split(',')

    """ Slide type is the last element of the list """
    slide_type = splited_url[-1]

    """ 
        Request the templates to the ICTV server 
        Raise IctvServerConnection, IctvChannelConfiguration
    """
    slides_templates = get_ictv_templates(str(pub.channel_id), chan_conf)

    if slide_type in slides_templates:
        slide_content = slides_templates[slide_type]
    else:
        # TODO : correct error msg
        raise IctvWrongSlideType("TODO ERROR")

    """ Copy extra data from ICTV specific form into the slide template """
    slide_data = {media_type: url for media_type, url in (media.split(':::') for media in splited_url[:-1])}
    for elem in slide_data:
        """ quick fix, incoherence in ICTV response (img vs image) """
        # TODO : remove quick fix
        if 'img' in elem:
            slide_content.pop(elem, None)
            slide_content['image-1'] = {'src': slide_data[elem]}
        else:
            slide_content[elem] = {'src': slide_data[elem]}

        # TODO : allow the user to choose the background size
        if 'background' in elem:
            slide_content[elem]['size'] = 'cover'

    """ Add publication data to the slide template """
    slide_content['title-1'] = {'text': pub.title}
    slide_content['text-1'] = {'text': pub.description}
    slide_content['subtitle-1'] = {'text': ''}
    # slide_content.pop('name', None)
    # slide_content.pop('description', None)

    return {'content': slide_content, 'template': 'template-' + slide_type, 'duration': -1}


def get_epoch(date):
    return date.replace(tzinfo=datetime.timezone.utc).timestamp()


def generate_capsule(pub):
    """
    Create the JSON representation of the capsule that will contain the slide
    :param pub: the publication
    :return: the JSON capsule
    """
    capsule = {'name': pub.title, 'theme': 'ictv', 'validity':
               [int(get_epoch(pub.date_from)), int(get_epoch(pub.date_until))]}
    # TODO : change the name of the capsule to unique name
    # TODO : give possibility to change the capsule theme
    return capsule


def run(pub, chan_conf, **kwargs):

    try:
        slide = generate_slide(chan_conf, pub)
    except (IctvServerConnection, IctvChannelConfiguration, IctvWrongSlideType) as e:
        return e.popup()

    capsule = generate_capsule(pub)

    """ Create new capsule on ICTV server on given channel """
    request_args = build_ictv_server_request_args(pub.channel_id, chan_conf, 'POST')
    capsules_url = request_args['url'] + '/capsules'
    # TODO : catch errors on request
    capsule_request = post(capsules_url, json=capsule, headers=request_args['headers'])

    """ Check if the capsule has been created """
    if capsule_request.status_code == 201:
        capsule_id = capsule_request.headers['Location'].split('/')[-1]
        slide_url = capsules_url + '/' + str(capsule_id) + '/slides'
        # TODO : catch errors on request
        slide_request = post(slide_url, json=slide, headers=request_args['headers'])
        if slide_request.status_code == 201:
            return None
        else:
            return IctvServerConnection(slide_request.status_code, msg='slide').popup()
    else:
        return IctvServerConnection(capsule_request.status_code, msg='capsule').popup()
