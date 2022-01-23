import feedparser


class FakerRssFeedParse:
    def valid_parser(*args, **kwargs):
        parser = feedparser.parse('''
        <?xml version="1.0" encoding="utf-8"?>
        <rss version="2.0">
        <channel>
            <title>Sample Feed</title>
            <description>For documentation &lt;em&gt;only&lt;/em&gt;</description>
            <link>http://example.org/</link>
            <pubDate>Sat, 07 Sep 2002 00:00:01 GMT</pubDate>
            
        <item>
            <title>First entry title</title>
            <link>http://example.org/entry/3</link>
            <description>Watch out for &lt;span style="background-image:
            url(javascript:window.location='http://example.org/')"&gt;nasty
            tricks&lt;/span&gt;</description>
            <pubDate>Thu, 05 Sep 2002 00:00:01 GMT</pubDate>
            <guid>http://example.org/entry/3</guid>
            <!-- other elements omitted from this example -->
            </item>
        </channel>
        </rss>
        ''')
        parser.status = 200
        parser.headers = {'content-type': 'xml'}
        return parser

    def invalid_parser_response_404(*args, **kwargs):
        parser = feedparser.parse('hello')
        parser.status = 404
        return parser

    def invalid_parser_response_json(*args, **kwargs):
        parser = feedparser.parse('hello')
        parser.status = 200
        parser.headers = {'content-type': 'json'}
        return parser


class FakeLimitError:
    FAKE_ERROR_LIMIT = 1
