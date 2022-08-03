def resource_url_builder(url: str, identifier: str):
    return url.rstrip("/") + "/" + identifier
