import json

from types import SimpleNamespace

from utils.CompositeLogger import CompositeLogger


def json_to_object(json_string):
    return json.loads(json_string, object_hook=lambda d: SimpleNamespace(**d))

def trunc_uuid(uuid):
    parts = str(uuid).split("-")
    return parts[0] + "..." + parts[-1]

def lbuffer_str(string, length=10):
    diff = length - len(string)

    if diff <= 0: return string
    
    buffer = " " * diff
    return buffer + string

def bytes_to_json(bytestring):
    # Decode UTF-8 bytes to Unicode, and convert single quotes
    # to double quotes to make it valid JSON
    value = bytestring.decode("utf8").replace("'", '"')

    data = json.loads(value)

    return json.dumps(data)

