**WARNING:** Unmaintained, check https://github.com/adbenitez/simplebot_manga for a similar project to
download manga.

***********************           
Simple Manga Downloader
***********************           

A tool to search and download manga from web sites, with support for several sites and languages.


Features
========

* Read manga offline without ads.
* Save bandwidth downloading only the necessary.
* Mangas are available in several languages.
* Multilingual interface.
* Continues canceled downloads from the same point it was interrupted.
* Downloaded ongoing mangas can be updated.
* Configurable.
* Documented.
* Always yours! Free as in freedom.


Currently supported sites
-------------------------

* **German (de):**

  * NineManga-de

* **English (en):**

  * NineManga-en
  * MangaReader
  * MangaAll
  * MangaNelo
  * MangaHere

* **Spanish (es):**

  * NineManga-es
  * HeavenManga
  * MangaDoor

* **Italian (it):**

  * NineManga-it

* **Portuguese (pt):**

  * NineManga-br

* **Russian (ru):**

  * NineManga-ru


Installation
============

The easiest way to install **smd** is using **pip**, open your terminal and execute the following command:

.. code-block:: bash
   
   $ pip install smd

Now the command ``smd`` should be available in your terminal.

.. note::

   For more help installing ``smd`` see the installation instructions in the `smd manual`_.


Examples
========

To select site and manga to download interactively just run:

.. code-block:: bash

   $ smd

To search mangaall.net for mangas containing the word 'first love' in its name, and select which one to download interactively:

.. code-block:: bash

   $ smd -s mangaall 'first love'

To download from chapter 10 to 20 (ignoring chapter 15) of 'Naruto':

.. code-block:: bash

   $ smd --chapters '10:20,!15' Naruto

To continue a previously canceled download:

.. code-block:: bash

   $ smd --continue

.. note::

   For more examples see the 'Quick start' subsection in the `smd manual`_.


Support
=======

To request new sites or if you are having issues, you can `open an issue <https://github.com/adbenitez/smd/issues/new>`_. For more information and tutorial read the `smd manual`_.


License
=======

This project is **free software**, licensed under the GPL3+ License - see the `LICENSE <https://github.com/adbenitez/smd/blob/master/LICENSE>`_ file for more details.


.. _smd manual: http://smd.readthedocs.io
