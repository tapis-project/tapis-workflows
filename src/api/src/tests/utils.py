import json

from conf.constants import ROOT_DIR


def load_fixture(filename, serialize=True):
    with open(f"{ROOT_DIR}/tests/fixtures/{filename}") as file:
        contents = file.read()

    if serialize:
        contents = json.loads(contents)

    return contents