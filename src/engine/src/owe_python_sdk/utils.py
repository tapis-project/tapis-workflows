def get_schema_extensions(plugins, _type, sub_type=None):
    schema_extensions = []
    for plugin in plugins:
        schema_extensions = schema_extensions + [ 
            ext.schema for ext in plugin.schema_extensions 
            if ext.type == _type 
            and (ext.sub_type == sub_type or sub_type == None)
        ]

    return schema_extensions