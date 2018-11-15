import json
import requests
import datetime
from utils import build_ictv_server_request_args, get_ictv_templates

FIELDS_UNAVAILABLE = ['ictv_data_form']

CONFIG_FIELDS = ['ictv_server_fqdn', 'ictv_channel_id', 'ictv_api_key']


def generate_ictv_dropdown_control():
    code = 'function tmp() {\n' \
            '    var chan_name = $("#chan_name").data()["chan_name"] + "_ictv_slide_type";\n' \
            '    $("input:radio[name="+chan_name+"]").click(function() {\n' \
            '       var name = $("#ictv_slide_choice_button input:radio:checked").val();\n' \
            '       $(".ictv_slide_choice").hide();\n' \
            '       $("#ictv_form_"+name).show();\n' \
            '    });\n' \
            '};\n'
    return code


def generate_ictv_dropdown(chan, templates):
    ret = '<div class="form-group" id="ictv_slide_choice_button">\n<meta id="chan_name" data-chan_name="' + chan.name + '">\n'
    ret = ret + '\t<button class="dropdown-toggle" type="button" data-toggle="dropdown" '\
                'onclick="tmp.bind(this)()">Slide Layout<span class="caret"></span></button>\n'
    ret = ret + '\t<ul class="dropdown-menu">\n'
    for index, temp in enumerate(templates):
        ret = ret + '\t\t<li>\n\t\t\t<div class = "form-check">\n'
        ret = ret + '\t\t\t\t<input class="form-check-input" type="radio" name="' + chan.name +\
              '_ictv_slide_type" id="ictv_slide_type_' + temp + '" value="' +\
               temp + '" ' + ('checked' if index == 0 else '') + '>\n'
        ret = ret + '\t\t\t\t<label class="form-check-label" for="ictv_slide_type_' + temp +\
                    '">' + templates[temp]["description"] + '</label>\n\t\t\t</div>\n\t\t</li>\n'

    ret = ret + '\t</ul>\n</div>\n'

    return ret


def generate_ictv_data_form(chan, templates):
    ret = ''

    for index, temp in enumerate(templates):
        ret = ret + '<div id=\"ictv_form_' + temp + '\" class=\"ictv_slide_choice\" ' + \
              ('style=\"display: none;\"' if index != 0 else '') + '>\n'
        ret = ret + '\t<h5>' + templates[temp]['name'] + '</h5>\n'

        for field in templates[temp]:
            if field != 'description' and field != 'name' and 'subtitle' not in field and 'title' not in field and \
                    'text' not in field:
                ret = ret + '\t<div class="form-group">\n'
                ret = ret + '\t\t<label for="' + chan.name + '_data_' + temp + '_' + field + \
                      '">' + field + '</label><br>\n'
                ret = ret + '\t\t<input type="text" name="' + chan.name + '_data_' + temp + '_' + field +\
                      '" id="' + chan.name + '_data_' + temp + '_' + field + '" class="form-control">\n'
                ret = ret + '\t</div>\n'

        ret = ret + '</div>\n'

    return ret


def generate_ictv_fields(chan):
    templates = get_ictv_templates(chan.config)
    return {'dropdown': generate_ictv_dropdown(chan, templates), 'data': generate_ictv_data_form(chan, templates),
            'control': generate_ictv_dropdown_control()}


def generate_slide(chan_conf, pub):
    splited_url = pub.link_url.split(',')
    slide_type = splited_url[-1]
    slide_content = get_ictv_templates(chan_conf)[slide_type]
    slide_data = {j: k for j, k in (i.split(':::') for i in splited_url[:-1])}
    for elem in slide_data:
        """ quick fix, incoherence in ICTV response (img vs image) """
        if 'img' in elem:
            slide_content.pop(elem, None)
            slide_content['image-1'] = {'src': slide_data[elem]}
        else:
            slide_content[elem] = {'src': slide_data[elem]}
        if 'background' in elem:
            slide_content[elem]['size'] = 'cover'
    slide_content['title-1'] = {'text': pub.title}
    slide_content['text-1'] = {'text': pub.description}
    slide_content['subtitle-1'] = {'text': ''}

    return {'content': slide_content, 'template': 'template-'+slide_type, 'duration': -1}


def get_epoch(date):
    return date.replace(tzinfo=datetime.timezone.utc).timestamp()


def generate_capsule(pub):
    """
    Create the JSON representation of a given publication
    :param pub: the publication
    :return: the JSON capsule
    """
    capsule = {'name': pub.title, 'theme': 'ictv', 'validity':
        [int(get_epoch(pub.date_from)), int(get_epoch(pub.date_until))]}
    # TODO : change the name of the capsule to unique name
    # TODO : give possibility to change the capsule theme
    return capsule


def run(pub, chan_conf, **kwargs):
    json_data = json.loads(chan_conf)

    """ Check channel config """
    for i in json_data:
        if i is None:
            pass
            # TODO : popup with error

    slide = generate_slide(chan_conf, pub)
    capsule = generate_capsule(pub)

    """ Create new capsule on ICTV server on given channel """
    request_args = build_ictv_server_request_args(chan_conf, 'POST')
    capsules_url = request_args['url'] + '/capsules'
    # TODO : catch errors on request
    capsule_request = requests.post(capsules_url, json=capsule, headers=request_args['headers'])

    """ Check if the capsule has been created, if true : send the slide, else : prompt popup """
    if capsule_request.status_code == 201:
        capsule_id = capsule_request.headers['Location'].split('/')
        capsule_id = capsule_id[len(capsule_id) - 1]
        slide_url = capsules_url + '/' + str(capsule_id) + '/slides'
        # TODO : catch errors on request
        slide_request = requests.post(slide_url, json=slide, headers=request_args['headers'])
        if slide_request.status_code == 201:
            # TODO : display popup
            print('Slide created')
            pass
        else:
            # TODO : display popup with error
            print('error with slide creation')
            pass
    else:
        # TODO : raise popup on superform
        error_str = 'capsule error'
        if capsule_request.status_code == 400:
            error_str = 'The capsule was misformed\n'
        elif capsule_request.status_code == 403:
            error_str = 'Bad authentication: you should check the ICTV API key in the channel configuration\n'
        print(error_str)

