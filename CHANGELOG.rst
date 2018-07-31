=================================
Simple Manga Downloader Changelog
=================================


Version 1.6.0
-------------

Released on August ??, 2018

* **New:** Now ``smd`` is *smarter*, it keeps metadata about the mangas and remember download status, downloading only missing or incomplete chapters, also useful to download new chapters from ongoing mangas.
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
