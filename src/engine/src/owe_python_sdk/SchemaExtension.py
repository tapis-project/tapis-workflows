class SchemaExtension:
    def __init__(self, _type, sub_type=None, schema={}):
        self.type = _type
        self.sub_type = sub_type
        self.schema = schema