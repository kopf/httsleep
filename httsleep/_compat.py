import sys


PY3 = sys.version_info[0] >= 3


if PY3:
    text_type = str
    string_types = (str,)
    integer_types = (int,)
else:
    text_type = unicode
    string_types = (str, unicode)
    integer_types = (int, long)
