from json.decoder import JSONDecodeError

from utils import bytes_to_json, json_to_object


class Context:
    def __init__(self, body):
        self = json_to_object(bytes_to_json(body))