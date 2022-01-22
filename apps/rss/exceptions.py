class InvalidFeedURL(Exception):
    default_message = 'Feed URL is invalid'

    def __init__(self, message=None, *args, **kwargs):
        self.message = message if message else self.default_message
