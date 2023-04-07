import json

from types import SimpleNamespace

from conf.constants import FLAVORS
# from errors import InvalidFlavorError
from core.tasks.Flavor import Flavor
from utils.CompositeLogger import CompositeLogger # NOTE imported to re-export


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

def get_flavor(flavor: str):
    if flavor not in FLAVORS:
        raise Exception(f"Invalid Flavor Error | Recieved: {flavor} | Expected: oneOf {[key for key in FLAVORS.keys()]}")

    return Flavor(**FLAVORS[flavor])