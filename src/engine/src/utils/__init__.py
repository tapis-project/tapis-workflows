import json

from importlib import import_module

from conf.constants import FLAVORS
# from errors import InvalidFlavorError
from tasks.Flavor import Flavor
from utils.CompositeLogger import CompositeLogger # NOTE imported to re-export


# def json_to_object(json_string):
#     return json.loads(json_string, object_hook=lambda d: SimpleNamespace(**d))

def trunc_uuid(uuid):
    parts = str(uuid).split("-")
    return parts[0] + "..." + parts[-1]

def lbuffer_str(string, length=10):
    diff = length - len(string)

    if diff <= 0: return string
    
    buffer = " " * diff
    return string + buffer

def serialize_request(bytestring):
    # DELETE THE BELOW BY: 2024/10/31
    # OLD Caused a serialization bug. But may have had use? 
    # value = bytestring.decode("utf8").replace("'", '"') 

    # Decode UTF-8 bytes to Unicode, and convert single quotes
    # to double quotes to make it valid JSON
    value = bytestring.decode("utf8")

    data = json.loads(value)

    return data

def get_flavor(flavor: str):
    if flavor not in FLAVORS:
        raise Exception(f"Invalid Flavor Error | Recieved: {flavor} | Expected: oneOf {[key for key in FLAVORS.keys()]}")

    return Flavor(**FLAVORS[flavor])

def load_plugins(plugin_names):
    contrib_prefix = "contrib"
    plugins = []
    for plugin_name in plugin_names:
        if "contrib/" in plugin_name:
            module_name = plugin_name.replace("contrib/", "")
            module = import_module(f"{contrib_prefix}.{module_name}.plugin")
            plugin_class = getattr(module, "plugin", None)
            if plugin_class != None: plugins.append(plugin_class(plugin_name))
            continue

        # TODO handle non-contrib plugins

    return plugins