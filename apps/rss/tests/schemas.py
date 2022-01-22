from helper.test import generate_list_schema_schema

rss_feed_schema = {
    'id': {'type': 'string', 'required': True, 'nullable': False},
    'title': {'type': 'string', 'required': True, 'nullable': True},
    'feed_url': {'type': 'string', 'required': True, 'nullable': False},
    'description': {'type': 'string', 'required': True, 'nullable': False},
    'last_update': {'type': 'string', 'required': True, 'nullable': False},
    'last_checked': {'type': 'string', 'required': True, 'nullable': False},
    'number_of_unseen_entries': {'type': 'integer', 'required': True, 'nullable': False},
    'number_of_followers': {'type': 'integer', 'required': True, 'nullable': False},
    'is_followed': {'type': 'boolean', 'required': True, 'nullable': False},
    'is_active': {'type': 'boolean', 'required': True, 'nullable': False},
}
rss_feed_list_schema = generate_list_schema_schema(rss_feed_schema)
