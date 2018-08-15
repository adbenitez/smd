.. _tutorial:

========
Tutorial
========

This tutorial will give you some advice on how to install and use the :abbr:`smd (Simple Manga Downloader)` application.

Requirements
------------

To use :abbr:`smd (Simple Manga Downloader)` you need to have **Python 3** installed in your machine. To know if you have python installed run the following command in your terminal:

.. code-block:: bash

  $ python3 --version

If you don't see a message like "``Python 3.X.X``" you have to install **Python 3**, for help installing it, read this `python installation guide`_.

.. _python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


Installation
------------

The more easy way to install :abbr:`smd (Simple Manga Downloader)` is using ``pip``, open your terminal and execute the following command:

.. code-block:: bash

  $ pip3 install smd

or

.. code-block:: bash

  $ python3 -m pip install smd
  
To install :abbr:`smd (Simple Manga Downloader)` from source extract the file ``smd-X.X.X.tar.gz`` (where X represents the version numbers), then open your terminal inside the extracted folder and execute the following command:
  
.. code-block:: bash
  
   $ python3 setup.py install

Once installed, the command ``smd`` should be available in your terminal. To test if the application was installed correctly, run the following command:

.. code-block:: bash
  
   $ smd --help

or

.. code-block:: bash
  
   $ python3 -m smd --help

You should see the :abbr:`smd (Simple Manga Downloader)` help.

.. note::
   If you have troubles with the installation read this `tutorial about installing packages in python <https://packaging.python.org/tutorials/installing-packages/>`_.


Upgrading
---------

To check for new versions of :abbr:`smd (Simple Manga Downloader)` and upgrade it use the following command:

.. code-block:: bash

  $ pip3 install --upgrade smd

or

.. code-block:: bash

  $ python3 -m pip install --upgrade smd
  

Quick start
-----------

This section have some examples to showcase the most common uses of :abbr:`smd (Simple Manga Downloader)`.

To select site and manga interactively just run:

.. code-block:: bash

   $ smd

To select site interactively and search (and download) 'One Piece':

.. code-block:: bash

   $ smd 'One Piece'

To search mangaall.net for mangas containing the word 'love' in its name, and select which one to download interactively:

.. code-block:: bash

   $ smd -s mangaall love

To select a site with *English* language, and search/download 'Bleach':

.. code-block:: bash

   $ smd --lang en Bleach

To download from chapter 10th to 20th (ignoring chapter 15th) of 'Naruto':

.. code-block:: bash

   $ smd --chapters '10:20,!15' Naruto

.. warning::
   Chapters are enumerated based on they order in the chapter list, so this number may not match the chapter title (e.g. if there are a chapter titled "Episode 15.5" and actually it is the chapter 16 in the list, you should use "``smd --chapter 16``" to download it)

To download from first chapter to 10th and the last chapter of 'Death Note':

.. code-block:: bash

   $ smd --chapters :10,-1 'Death Note'

To select from a list of previously canceled downloads and continue with them:

.. code-block:: bash

   $ smd --continue

To continue with the given previously canceled downloads:

.. code-block:: bash

   $ smd --continue /path/to/the/canceled/download

To select from a list of previously downloaded ongoing mangas and update them:

.. code-block:: bash

   $ smd --update

To list all supported sites that you can use with the option ``-s``:

.. code-block:: bash

   $ smd -l

To list supported *Spanish* sites:

.. code-block:: bash

   $ smd --lang es -l

To see all available options use:

.. code-block:: bash

   $ smd -h


SMD data folder
---------------

:abbr:`smd (Simple Manga Downloader)` creates a folder called ``smd`` in your user home folder (on GNU/Linux it is ``/home/<your user name>`` on Windows it is ``C:\Users\<your user name>``). Inside this folder is located some useful files like the :abbr:`smd (Simple Manga Downloader)` is configuration file and the log files that keep track of errors.

Configuration File
^^^^^^^^^^^^^^^^^^

The configuration file is named ``smd.cfg``. At the time the only configurable options are:

* ``language``: this set the language of the application, can be set to ``en`` (English), ``es`` (Spanish) or ``SYSTEM`` (to use the language of the system, this is the default).
* ``manga_dir``: use this option to set the path to the folder where the program should download and look for manga folders, by default is set to '.' (dot) which means that the current working directory will be used.

Log files
^^^^^^^^^

The log of the more recent execution will be saved on ``smd.log``, when the size of this file grows the older logs are moved to ``smd.log.1``.
