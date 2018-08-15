# -*- coding: utf-8 -*-
"""
.. module:: utils

This module provides utility functions and classes.

.. moduleauthor:: Asiel Díaz Benítez <asieldbenitez@gmail.com>

"""
from abc import ABC, abstractmethod
import configparser
import json
import logging
import os

from random import choice
import sys
import typing

if typing.TYPE_CHECKING:
    from typing import Callable, Iterator, List, TypeVar
    import bs4    # type: ignore
    import smd
    NoReturn = TypeVar('NoReturn')

    def _(msg: str) -> str:
        return msg


def persistent_operation(function: 'Callable') -> 'Callable':
    """Makes the decorated function to excecute again on KeyboardInterrupt
    or SystemExit exceptions.
    """
    def _wrapper(*args, **kargs):
        try:
            return function(*args, **kargs)
        except (KeyboardInterrupt, SystemExit):
            _wrapper(*args, **kargs)
            raise
    return _wrapper


class MetaFolder(ABC):

    """Abstract class representing a meta data folder."""

    data_filename = 'data.json'

    def __init__(self, path: str) -> None:
        """
        :param path: the path to the meta data folder.
        """
        self.path = path
        self._ignored = ['_ignored', 'path']

    @staticmethod
    def _load_from_folder(obj: 'MetaFolder') -> None:
        """Loads the given object is meta data"""
        with open(obj.data_file) as data_fh:
            data = json.load(data_fh)
        for key in data:
            setattr(obj, key, data[key])

    @property
    def data_file(self) -> str:
        """The path to the meta data file."""
        return os.path.join(self.path, self.data_filename)

    @staticmethod
    @abstractmethod
    def from_folder(path: str) -> 'MetaFolder':
        """Creates a ``MetaFolder`` instance from a folder path.

        :param path: path to a folder.
        :return: the created instance.
        """
        pass

    @classmethod
    def is_valid(cls, path: str) -> bool:
        """Checks whether the given path is a valid MetaFolder or not.

        :param path: path to a folder.
        :return: ``True`` if the given folder is valid, ``False``
                 otherwise.
        """
        return os.path.isfile(os.path.join(path, cls.data_filename))

    @persistent_operation
    def save_data(self) -> None:
        """Saves meta data."""
        data = {k:v for k, v in self.__dict__.items()
                if k not in self._ignored}
        with open(self.data_file, 'w') as data_fh:
            json.dump(data, data_fh)


class Chapter(MetaFolder):

    """Class representing a chapter folder."""

    data_filename = 'chapter.json'

    def __init__(self, path: str, title: str, url: str) -> None:
        """
        :param path: the path to the chapter folder.
        :param title: the chapter title.
        :param url: the chapter URL.
        """
        super().__init__(path)
        self.title = title
        self.url = url
        self.current = -1  # type: int
        self.images = []   # type: List[str]

    def __str__(self) -> str:
        return self.title

    def __repr__(self) -> str:
        return '({}, {}, {})'.format(self.title, self.url, self.current)

    @staticmethod
    def from_folder(path: str) -> 'Chapter':
        """Creates a :class:`~smd.utils.Chapter` instance from a folder path.

        :param path: the path to the chapter folder.
        :return: the created :class:`~smd.utils.Chapter` instance.
        """
        chap = Chapter(path, '', '')
        Chapter._load_from_folder(chap)
        return chap


class Config:

    """Class to manage the configuration of ``smd``"""

    def __init__(self, path: str) -> None:
        """
        :param path: the path to the configuration file.
        """
        self.path = path
        self._parser = configparser.ConfigParser()
        if self.exists():
            self.load()
        else:
            self.reset()

    def __getitem__(self, key: str):
        if key in self._parser:
            return self._parser[key]
        else:
            return self._parser['DEFAULT'][key]

    def __setitem__(self, key: str, value: str) -> None:
        self._parser['DEFAULT'][key] = value

    def exists(self) -> bool:
        """Checks if the configuration file exists.

        :return: ``True`` if the configuration file exists, ``False``
                 otherwise.
        """
        return os.path.exists(self.path)

    def load(self) -> 'List[str]':
        """Loads the configuration from disk.

        :return: a list with the loaded configuration files.
        """
        return self._parser.read(self.path)

    def reset(self) -> None:
        """Resets all configuration values to the defaults."""
        default = self._parser['DEFAULT']
        default['language'] = 'SYSTEM'
        default['manga_dir'] = '.'

    def save(self) -> None:
        """Saves the configuration to disk."""
        with open(self.path, 'w') as config_fd:
            self._parser.write(config_fd)


class ConsoleFilter(logging.Filter):

    """A filter to avoid showing exceptions stack traces text in user's
    terminal."""

    @staticmethod
    def filter(record: logging.LogRecord) -> bool:
        """Removes exception stack traces information."""
        record.exc_info = None
        record.exc_text = None  # type: ignore
        return True


class Manga(MetaFolder):

    """Class representing a manga folder."""

    data_filename = 'manga.json'

    def __init__(self, path: str, title: str, url: str, site: str) -> None:
        """
        :param path: the path to the manga folder.
        :param title: the manga title.
        :param url: the manga URL.
        :param site: the name of the downloader of this manga.
        """
        super().__init__(path)
        self.title = title
        self.url = url
        self.site = site

    def __str__(self) -> str:
        return self.title

    def __repr__(self) -> str:
        return '({}, {}, {})'.format(self.title, self.url, self.site)

    def chapters(self) -> 'Iterator[Chapter]':
        """Returns an iterator that yields chapters found in the manga
        folder"""
        for chap in os.listdir(self.path):
            path = os.path.join(self.path, chap)
            if Chapter.is_valid(path):
                yield Chapter.from_folder(path)

    @staticmethod
    def from_folder(path: str) -> 'Manga':
        """Creates a :class:`~smd.utils.Manga` instance from a folder path.

        :param path: the path to the manga folder.
        :return: the created :class:`~smd.utils.Manga` instance.
        """
        manga = Manga(path, '', '', '')
        Manga._load_from_folder(manga)
        return manga

    def get_new_chapter_path(self) -> str:
        """Generates a nonexistent chapter path.
        :return: a path to a chapter folder that don't already exists.
        """
        chap_num = 1
        path = os.path.join(self.path, str(chap_num).zfill(6))
        while os.path.exists(path):
            chap_num += 1
            path = os.path.join(self.path, str(chap_num).zfill(6))
        return path


def die(msg: str, status: int = 1) -> 'NoReturn':
    """Shows a message and terminates the program execution.

    :param msg: the message to show before terminating the application.
    :param status: the exit code.
    """
    print(msg)
    sys.exit(status)


def get_mangas(path: str) -> 'List[Manga]':
    """Gets all mangas found in the given folder.

    :param path: path to a folder.
    :return: the list of mangas found.
    """
    return [Manga.from_folder(os.path.join(path, name))
            for name in os.listdir(path)
            if Manga.is_valid(os.path.join(path, name))]


def get_text(tag: 'bs4.Tag') -> str:
    """Extracts the text from a BeautifulSoup tag.

    :param tag: the tag to extract text from.
    :return: the tag text without ``\\n`` and with trailing white spaces
             removed.
    """
    return tag.get_text().replace('\n', ' ').strip()


def mkdir(dirname: str, basename: str) -> str:
    """Tries to create a new folder ``basename`` in the folder ``dirname``
    if the name of the new folder is invalid or already exists ask the
    user to enter a new one.

    :param dirname: the parent directory of the new folder.
    :param basename: the name of the folder.
    :return: the path of the new created folder.
    """
    while True:
        path = os.path.join(dirname, basename)
        if os.path.exists(path):
            print(_("[*] ERROR - Can't create folder: '{}' already exists.")
                  .format(basename))
        else:
            try:
                os.mkdir(path)
                break
            except FileNotFoundError:
                print(_("[*] ERROR - Can't create folder '{}': Invalid name.")
                      .format(basename))
        basename = input(_("Enter a new folder name:"))
    return path


def random_ua() -> str:
    """Generates a random User-Agent HTTP header."""
    os = choice(('X11; Ubuntu; Linux x86_64;',
                  'Windows NT 10.0; Win64; x64;',
                 'Macintosh; Intel Mac OS X 10.7;'))
    browser_version = choice(('60.0', '61.0', '62.0', '59.0'))
    return 'Mozilla/5.0 ({0} rv:{1}) Gecko/20100101 Firefox/{1}' \
        .format(os, browser_version)


def select_chapters(chapters: 'List[Chapter]',
                    selectors_str: str) -> 'List[Chapter]':
    """Selects the chapters specified in the given selectors.

    :param chapters: a list of chapters.
    :param selectors: a string of comma-separated selectors.
    :return: a list of selected chapters.
    """
    if not selectors_str:
        return chapters
    selectors = selectors_str.split(',')
    chaps = set()
    ignored_chaps = set()
    for selector in selectors:
        ignore = False
        selector = selector.replace(' ', '')
        selec_str = selector[:]
        if selec_str.startswith('!'):
            ignore = True
            selec_str = selec_str[1:]
        if set(selec_str) - set('1234567890-:'):
            die(_("[*] ERROR - Invalid chapter selector: '{}'").format(selector))
        try:
            selec = selec_str.split(':')
            if selec[0]:
                i = int(selec[0])
                if i > 0:
                    selec[0] = str(i-1)
            selec_str = ':'.join(selec)
            selec_chaps = eval("chapters[{}]".format(selec_str))
            if isinstance(selec_chaps, list):
                if not selec_chaps:
                    die(_(
                        "[*] ERROR - Selector '{}' did not selected any chapters."
                    ).format(selector))
                elif ignore:
                    ignored_chaps.update(selec_chaps)
                else:
                    chaps.update(selec_chaps)
            else:
                if ignore:
                    ignored_chaps.add(selec_chaps)
                else:
                    chaps.add(selec_chaps)
        except (SyntaxError, ValueError):
            die(_("[*] ERROR - Invalid chapter selector: '{}'").format(selector))
        except IndexError:
            die(_("[*] ERROR - Chapter selector out of range: '{}'")
                .format(selector))
    if not chaps:
        chaps = set(chapters)
    return sorted(chaps - ignored_chaps, key=lambda c: chapters.index(c))


def select_mangas(mangas: 'List[Manga]', list_header: str = 'Found:',
                  prompt_msg: str = 'Select a manga',
                  multiple: bool = True) -> 'List[Manga]':
    """Lets the user select a manga from the given list, keeps asking if
    the user enters invalid option numbers.

    :param mangas: a list of mangas.
    :param list_header: the header message to show on top of the list.
    :param prompt_msg: the message prompt.
    :param multiple: if ``True`` allows to select multiple choices.
    :return: the selected manga (or mangas).
    """
    print(list_header)
    mlen = len(mangas)
    if multiple:
        mlen += 1
    dcount = len(str(mlen))
    for i, manga in enumerate(mangas, 1):
        print("{}. {}".format(str(i).rjust(dcount), manga))
    if multiple:
        print("{}. {}".format(mlen, _('[SELECT ALL]')))
    while True:
        try:
            selec_str = input(prompt_msg+" [1-{}]:".format(mlen))
            if ',' in selec_str:
                selec = [int(s) for s in selec_str.split(',')]
            else:
                selec = [int(s) for s in selec_str.split()]
            for i in selec:
                if i <= 0:
                    raise ValueError
            if multiple:
                if mlen in selec:
                    return mangas
                else:
                    return [mangas[i-1] for i in selec]
            elif len(selec) == 1 and selec[0] > 0 and selec[0] <= mlen:
                    return [mangas[selec[0]-1]]
        except ValueError:
            pass
        print(_("[*] ERROR - Invalid selection. Try again."))
