import json

from types import SimpleNamespace


def json_to_object(json_string):
    return json.loads(json_string, object_hook=lambda d: SimpleNamespace(**d))
