import os

def resource_url_builder(url, identifier):
    return os.path.join(url, identifier)
