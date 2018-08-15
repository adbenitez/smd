=================================
Simple Manga Downloader Changelog
=================================

Version 1.6.2
-------------

Released on August 15, 2018

* **Fix:** Fixed bug in ``smd.__init__.py`` file: :meth:`show_copyright` isn't in package :mod:`smd.utils` anymore.
* **New:** Code re-factorized with annotations, for static typing checking with ``mypy``.
* **New:** :func:`smd.downloader.Downloader.get` separated in two new functions :func:`~smd.downloader.Downloader.get_bytes` and :func:`~smd.downloader.Downloader.get_str`.
* **New:** Classes :class:`~smd.utils.Chapter` and :class:`~smd.utils.Manga` now use attributes instead of ``__setitem__`` and ``__getitem__`` for accessing meta data.
* **New:** Created :class:`smd.utils.MetaFolder` class base for :class:`~smd.utils.Chapter` and :class:`~smd.utils.Manga`.
* **New:** Removed variable ``smd.utlis.USER_AGENT`` and created function :func:`smd.utils.random_ua` instead.
* **New:** Chapters folders are now named using numbers to avoid invalid folder names.
* **New:** :func:`~smd.downloader.Downloader.search` now returns a list of :class:`~smd.utils.Manga` and :func:`~smd.downloader.Downloader.get_chapters` returns a list of :class:`~smd.utils.Chapter`
* **Fix:** Fixed localization setup to fallback to the default if the language set in the configuration file is not supported.


Version 1.6.1
-------------

Released on July 31, 2018

* **Fix:** Fixed function :func:`smd.utils.select_chapters` to return a ``list`` of chapters in the right order instead of an unordered set.


Version 1.6.0
-------------

Released on July 31, 2018

* **New:** Now ``smd`` is *smarter*, it keeps meta-data about the mangas and remember download status, downloading only missing or incomplete chapters, also useful to download new chapters from ongoing mangas.
* **New:** Added option ``--update`` (to get new chapters for ongoing mangas).
* **New:** Added option ``--continue`` (to resume a canceled manga download).
* **New:** Now ``smd`` have a multilingual interface, currently only *English* and *Spanish* languages are supported.
* **New:** Added configuration file to configure language, folder where to find and save mangas, etc.
* **New:** Added documentation to the project and integrated it with `Read the Docs <http://readthedocs.org>`_.
* **New:** Updated ``tests`` module.


Version 1.5.0
-------------

Released on July 18, 2018

* **New:** Added new option ``-d``  or ``--directory`` to set the place where to save mangas (default: working directory).
* **Fix:** If the manga title or chapter title are an invalid folder name, ask the user for a new name instead of crashing.
* **New:** Removed ``--start`` and ``--stop`` options in favor of a more powerful ``--chapters`` option. Now use ``--chapters 10:20`` instead of ``--start 10 --stop 20``.
* **New:** Log file now moved to ``[USER HOME]/smd/smd.log`` and log size limited.
* **New:** Now exception traces are sent only to log file and small messages to console.
* **New:** Added ``--verbose`` option to make the program print debug messages and error stack traces.
* **Fix:** On ConnectionResetError retry only a fixed number of times.
* **New:** Added new package to the project: ``tests`` for unit testing.


Previous versions
-----------------

Changes to previous versions were not tracked.
