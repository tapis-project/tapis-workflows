import json


def bytes_to_json(bytestring):
    # Decode UTF-8 bytes to Unicode, and convert single quotes
    # to double quotes to make it valid JSON
    value = bytestring.decode("utf8").replace("'", '"')

    data = json.loads(value)

    return json.dumps(data)
