from apps.account.tests.schemas import user_read_only_schema
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

entry_schema = {
    'id': {'type': 'string', 'required': True, 'nullable': False},
    'feed': {'type': 'string', 'required': True, 'nullable': False},
    'title': {'type': 'string', 'required': True, 'nullable': False},
    'url': {'type': 'string', 'required': True, 'nullable': True},
    'guid': {'type': 'string', 'required': True, 'nullable': True},
    'content': {'type': 'string', 'required': True, 'nullable': False},
    'publish_date': {'type': 'string', 'required': True, 'nullable': True},
    'is_bookmarked': {'type': 'boolean', 'required': True, 'nullable': False},
    'is_favourited': {'type': 'boolean', 'required': True, 'nullable': False},
}

entry_comment_schema = {
    'id': {'type': 'string', 'required': True, 'nullable': False},
    'entry_id': {'type': 'string', 'required': True, 'nullable': False},
    'user': {'type': 'dict', 'required': True, 'schema': user_read_only_schema},
    'body': {'type': 'string', 'required': True, 'nullable': False},
}

rss_feed_list_schema = generate_list_schema_schema(rss_feed_schema)
entry_list_schema = generate_list_schema_schema(entry_schema)
entry_comment_list_schema = generate_list_schema_schema(entry_comment_schema)
