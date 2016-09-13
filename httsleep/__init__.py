from ._compat import PY3

if PY3:
    from .async import async_httsleep as httsleep, AsyncHttSleeper as HttSleeper
else:
    from .main import httsleep, HttSleeper
