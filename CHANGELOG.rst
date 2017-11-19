httsleep Changelog
==================

Next Version
------------

Version 0.3.0
-------------
* The kwargs ``verify`` and ``session`` are now supported, allowing users of httsleep to
  specify these in the same way as when directly using the ``requests`` library.
* The shorthand kwargs (``status_code``, ``json``, ``jsonpath``, ``text``, ``callback``)
  have been removed.

Version 0.2.0
-------------
* The shorthand kwargs (``status_code``, ``json``, ``jsonpath``, ``text``, ``callback``)
  are now deprecated. Please use ``until`` exclusively.

Version 0.1.4
-------------
* Replace ``*args`` and ``**kwargs`` in httsleep wrapper with explicit args/kwargs, so
  they can be displayed in IDEs
* Documentation improvements

Version 0.1.3
-------------

* Fix docstring
* Documentation cleanup
* Replace markdown README with rst version

Version 0.1.2
-------------

* Fix url in setup.py

Version 0.1.1
-------------

* Added CHANGELOG
* Fix setup.py

Version 0.1
-----------

* Initial release
