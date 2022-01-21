def generate_list_schema_schema(object_schema):
    return {
        'next': {'type': 'string', 'required': True, 'nullable': True},
        'previous': {'type': 'string', 'required': True, 'nullable': True},
        'count': {'type': 'integer', 'required': True},
        'results': {'type': 'list', 'schema': {'type': 'dict', 'schema': object_schema}}
    }
