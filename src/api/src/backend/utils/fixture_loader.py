import json, os


FIXTURES_DIR = "./../fixtures/"

# JSON fixture loading util
def fixture_loader(fixture):
    dirname = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(dirname, f"{FIXTURES_DIR}{fixture}.json")
    with open(filename, "r") as f:
        return json.load(f)