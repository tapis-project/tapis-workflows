class Event:
    def __init__(self, _type, payload, **kwargs):
        self.type = _type
        self.payload = payload

        for key in kwargs.keys():
            setattr(self, key, kwargs[key])