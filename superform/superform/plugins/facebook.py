import facebook

FIELDS_UNAVAILABLE = ['Description','Link']

CONFIG_FIELDS = ["access_token"]


def run(publishing,channel_config):
    json_data = json.loads(channel_config)
    acc_tok = json_data['access_token']
    graph = facebook.GraphAPI(access_token=acc_tok)
    graph.put_object(parent_object='me', connection_name='feed', message=publishing.description,
                     link=publishing.link_url)
