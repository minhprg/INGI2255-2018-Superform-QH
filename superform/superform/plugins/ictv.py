import json

FIELDS_UNAVAILABLE = []

CONFIG_FIELDS = ["ICTV channels"]

def run(publishing,channel_config):
    json_data = json.loads(channel_config)
    buildings = json_data['ICTV channels']