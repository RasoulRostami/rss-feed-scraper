def generate_list_schema_schmea(object_schema):
    return {
        'next': {'type': 'string', 'required': True, 'nullable': True},
        'previous': {'type': 'string', 'required': True, 'nullable': True},
        'count': {'type': 'integer', 'required': True},
        'results': {'type': 'list', 'schema': {'type': 'dict', 'schema': object_schema}}
    }


sign_up_response_schema = {
    'access': {'type': 'string', 'required': True, 'nullable': False},
    'refresh': {'type': 'string', 'required': True, 'nullable': False},
}

user_info_schema = {
    "id": {'type': 'integer', 'required': True, 'nullable': False},
    "username": {'type': 'string', 'required': True, 'nullable': False},
    "email": {'type': 'string', 'required': True, 'nullable': False},
    "first_name": {'type': 'string', 'required': True, 'nullable': False},
    "last_name": {'type': 'string', 'required': True, 'nullable': False},
}
