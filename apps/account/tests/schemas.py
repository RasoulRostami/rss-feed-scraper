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

user_read_only_schema = {
    "id": {'type': 'integer', 'required': True, 'nullable': False},
    "username": {'type': 'string', 'required': True, 'nullable': False},
    "first_name": {'type': 'string', 'required': True, 'nullable': False},
    "last_name": {'type': 'string', 'required': True, 'nullable': False},
}
