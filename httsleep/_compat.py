import sys


PY2 = sys.version_info[0] == 2


if not PY2:
    text_type = str
    string_types = (str,)
    integer_types = (int,)

else:
    text_type = unicode
    string_types = (str, unicode)
    integer_types = (int, long)
