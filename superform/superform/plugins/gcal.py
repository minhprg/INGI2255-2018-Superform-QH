import json

FIELDS_UNAVAILABLE = []

CONFIG_FIELDS = ["Calendar link"]

def run(publishing,channel_config):
    json_data = json.loads(channel_config)
    agenda = json_data['Calendar link']