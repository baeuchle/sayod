"""Things for plain log protocoll"""


class PlainLog:
    LAST = "last"
    COUNT = "count"
    FIRST = "first"
    LIST = "list"

    @classmethod
    def add_options(cls, parser):
        parser.add_argument('--subject', required=False, default=[], nargs='*')
        parser.add_argument('--action',
                            help='specify which action should be read from the log',
                            default=cls.LIST,
                            choices=[cls.LAST, cls.COUNT, cls.FIRST, cls.LIST])
