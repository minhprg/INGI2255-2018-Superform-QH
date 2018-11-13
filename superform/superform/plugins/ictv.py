import json
import requests
import datetime
from utils import build_ictv_server_request_args, get_ictv_templates

FIELDS_UNAVAILABLE = []

CONFIG_FIELDS = ["ictv_server_fqdn", "ictv_channel_id", "ictv_api_key"]


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
    capsule = {'name': pub.title, 'theme': 'ictv', 'validity': [int(get_epoch(pub.date_from)), int(get_epoch(pub.date_until))]}
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
    # print(slide)
    capsule = generate_capsule(pub)
    # print(capsule)

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

