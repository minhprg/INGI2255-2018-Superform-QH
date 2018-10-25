import json
import requests
import datetime

FIELDS_UNAVAILABLE = []

CONFIG_FIELDS = ["ictv_server_fqdn", "ictv_channel_id", "ictv_api_key"]


def generate_slide(pub):
    content = {'title-1': {'text': pub.title}, 'subtitle-1': {'text': ''}, 'text-1':  {'text': pub.description}}
    slide = {'content': content, 'template': 'template-text-center', 'duration': -1}
    return slide


def get_epoch(date):
    return date.replace(tzinfo=datetime.timezone.utc).timestamp()


def generate_capsule(pub):
    """
    Create the JSON representation of a given publication
    :param pub: the pubication
    :return: the JSON capsule
    """
    capsule = {'name': pub.title, 'theme': 'ictv', 'validity': [int(get_epoch(pub.date_from)), int(get_epoch(pub.date_until))]}
    # TODO : change the name of the capsule to unique name
    # TODO : give possibility to change the capsule theme
    return capsule


def send_slide():
    return

def run(pub, chan_conf):
    json_data = json.loads(chan_conf)
    print(json_data)
    print(pub.__dict__)

    """ Check channel config """
    for i in json_data:
        if i is None:
            pass
            # TODO : popup with error

    slide = generate_slide(pub)
    print(slide)
    capsule = generate_capsule(pub)
    print(capsule)

    """ Create new capsule on ICTV server on given channel """
    base_url = 'http://' + json_data['ictv_server_fqdn'] + '/channels/' + json_data['ictv_channel_id'] + '/api/capsules'
    headers = {'accept': 'application/json', 'Content-Type': 'application/json',
               'X-ICTV-editor-API-Key': json_data['ictv_api_key']}

    capsule_request = requests.post(base_url, json=capsule, headers=headers)

    """ Check if the capsule has been created, if true : send the slide, else : prompt popup """
    if capsule_request.status_code == 201:
        capsule_id = capsule_request.headers['Location'].split('/')
        capsule_id = capsule_id[len(capsule_id) - 1]
        slide_url = base_url + '/' + str(capsule_id) + '/slides'
        slide_request = requests.post(slide_url, json=slide, headers=headers)
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

