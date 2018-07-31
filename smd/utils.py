# -*- coding: utf-8 -*-
"""
.. module:: utils

This module provides utility functions and classes.

.. moduleauthor:: Asiel Díaz Benítez <asieldbenitez@gmail.com>

"""


import configparser
import json
import os
from os.path import (exists as pexists, isdir as pisdir, isfile as pisfile,
                     join as pjoin)
from random import choice
import sys

_OS = choice(('X11; Ubuntu; Linux x86_64;',
              'Windows NT 10.0; Win64; x64;',
              'Macintosh; Intel Mac OS X 10.7;'))
_B_VERSION = choice(('60.0', '61.0', '62.0', '59.0'))
USER_AGENT = 'Mozilla/5.0 ({0} rv:{1}) Gecko/20100101 Firefox/{1}'\
             .format(_OS, _B_VERSION)


class Chapter:

    """Class representing a chapter folder."""

    _filename = 'chapter.json'

    def __init__(self, path, title=None, url=None):
        """
        :param str path: the path to the chapter folder.
        :param str title: the chapter title.
        :param str url: the chapter URL.
        """
        self.path = path
        self._data_file = pjoin(path, self._filename)
        self.data = {
            'title': title,
            'url': url,
            'current': -1,
            'images': []
        }

    def __str__(self):
        return self.data['title']

    def __repr__(self):
        return '({}, {}, {})'.format(
            self['title'], self['url'], self['current'])

    def __setitem__(self, name, value):
        self.data[name] = value

    def __getitem__(self, name):
        return self.data[name]

    @staticmethod
    def from_folder(path):
        """Creates a :class:`~smd.utils.Chapter` instance from a folder path.

        :param str path: the path to the chapter folder.
        :return: the created :class:`~smd.utils.Chapter` instance.
        """
        chap = Chapter(path)
        with open(chap._data_file) as data_fh:
            chap.data = json.load(data_fh)
        return chap

    @classmethod
    def is_chapter(cls, chapter_path):
        """Checks whether the given folder is a chapter folder or not.

        :param str chapter_path: path to a folder.
        :return: ``True`` if the given folder is a chapter, ``False``
                 otherwise.
        """
        return pisfile(pjoin(chapter_path, cls._filename))

    def save_data(self):
        """Saves chapter meta data."""
        with open(self._data_file, 'w') as data_fh:
            json.dump(self.data, data_fh)


class Config:

    """Class to manage the configuration of ``smd``"""

    def __init__(self, path):
        """
        :param str path: the path to the configuration file.
        """
        self.path = path
        self._parser = configparser.ConfigParser()
        if self.exists():
            self.load()
        else:
            self.reset()

    def __getitem__(self, key):
        if key in self._parser:
            return self._parser[key]
        else:
            return self._parser['DEFAULT'][key]

    def __setitem__(self, key, value):
        self._parser['DEFAULT'][key] = value

    def exists(self):
        """Checks if the configuration file already exists.

        :return: ``True`` if the configuration file exists, ``False``
                 otherwise.
        """
        return os.path.exists(self.path)

    def load(self):
        """Loads the configuration from disk.

        :return: a list with the loaded configuration files.
        """
        return self._parser.read(self.path)

    def reset(self):
        """Resets all configuration values to the defaults."""
        default = self._parser['DEFAULT']
        default['language'] = 'SYSTEM'
        default['manga_dir'] = '.'

    def save(self):
        """Saves the configuration to disk."""
        with open(self.path, 'w') as config_fd:
            self._parser.write(config_fd)


class ConsoleFilter:

    """A filter to avoid showing exceptions stack traces text in user's
    terminal."""

    @staticmethod
    def filter(record):
        """Removes exception stack traces information."""
        record.exc_info = None
        record.exc_text = None
        return True


class Manga:

    """Class representing a manga folder."""

    _filename = 'manga.json'

    def __init__(self, path, title=None, url=None, site=None):
        """
        :param str path: the path to the manga folder.
        :param str title: the manga title.
        :param str url: the manga URL.
        :param str site: the name of the downloader for the site of this manga.
        """
        self.path = path
        self._data_file = pjoin(path, self._filename)
        self.data = {
            'title': title,
            'url': url,
            'site': site,
        }

    @property
    def chapters(self):
        """The chapters found in the manga folder"""
        return [Chapter.from_folder(pjoin(self.path, chap))
                for chap in os.listdir(self.path)
                if Chapter.is_chapter(pjoin(self.path, chap))]

    def __str__(self):
        return self.data['title']

    def __repr__(self):
        return '({}, {}, {})'.format(
            self['title'], self['url'], self['site'])

    def __setitem__(self, name, value):
        self.data[name] = value

    def __getitem__(self, name):
        return self.data[name]

    def chapters_iter(self):
        """Returns an iterator that yields chapters found in the manga
        folder"""
        for chap in os.listdir(self.path):
            path = pjoin(self.path, chap)
            if Chapter.is_chapter(path):
                yield Chapter.from_folder(path)

    @staticmethod
    def from_folder(path):
        """Creates a :class:`~smd.utils.Manga` instance from a folder path.

        :param str path: the path to the manga folder.
        :return: the created :class:`~smd.utils.Manga` instance.
        """
        manga = Manga(path)
        with open(manga._data_file) as data_fh:
            manga.data = json.load(data_fh)
        return manga

    @classmethod
    def is_manga(cls, manga_path):
        """Checks whether the given folder is a manga folder or not.

        :param str manga_path: path to a folder.
        :return: ``True`` if the given folder is a manga, ``False`` otherwise.
        """
        return pisfile(pjoin(manga_path, cls._filename))

    def save_data(self):
        """Saves manga meta data."""
        with open(self._data_file, 'w') as data_fh:
            json.dump(self.data, data_fh)


def create_config_folder():
    """Creates the application is configuration folder.

    :return: the path to the configuration folder.
    :rtype: str
    """
    conf_dir = pjoin(os.path.expanduser('~'), 'smd')
    if pexists(conf_dir):
        if not pisdir(conf_dir):
            die(_("CRITICAL ERROR - Can't create configuration folder '{}'.")
                .format(conf_dir))
    else:
        try:
            os.mkdir(conf_dir)
        except FileNotFoundError:
            die(_("CRITICAL ERROR - Can't create configuration folder '{}'.")
                .format(conf_dir))
    return conf_dir


def die(msg, status=1):
    """Shows a message and terminates the program execution.

    :param str msg: the message to show before terminating the application.
    :param int status: the exit code.
    """
    print(msg)
    sys.exit(status)


def download(downloaders, manga, chapter_selectors, tryall):
    """Downloads the given manga using one of the given downloaders.

    :param list downloaders: the downloaders.
    :param str manga: the manga name.
    :param str chapter_selectors: the chapters to download.
    :param bool tryall: when ``True`` if a downloader fail, then tries other
                        downloaders.
    :return: ``True`` if the download succeeded, ``False`` otherwise.
    """
    downloader = downloaders.pop(0)
    if not downloader.download(manga, chapter_selectors):
        downloader.logger.error(_("Download have failed :("))
        if tryall and downloaders:
            downl = select_downloader(downloaders)
            downloaders.remove(downl)
            downloaders.insert(0, downl)
            return download(downloaders, manga, chapter_selectors, tryall)
        else:
            return False
    else:
        return True


def filter_downloaders(lang, downloaders):
    """Selects from the given list, the downloaders with the given language.

    :param str lang: the language of the downloaders to select.
    :param list downloaders: a list of downloaders
                             (:class:`~smd.downloader.Downloader`).
    :return: a list of downloaders with the given language.
    """
    if not lang:
        return downloaders
    lang = lang.lower()
    langs = sorted(set(d.lang for d in downloaders))
    if lang not in langs:
        print(_("ERROR - Unknow language: '{}'").format(lang))
        lang = select_lang(langs)
    return [d for d in downloaders if d.lang == lang]


def get_mangas(path):
    """Gets all mangas found in the given folder.

    :param str path: path to a folder.
    :return: the list of mangas found.
    """
    return [Manga.from_folder(pjoin(path, name)) for name in os.listdir(path)
            if Manga.is_manga(pjoin(path, name))]


def get_text(tag):
    """Extracts the text from a BeautifulSoup tag.

    :param tag: the tag to extract text from.
    :type tag: :class:`bs4.Tag`
    :return: the tag text without ``\\n`` and with trailing white spaces
             removed.
    """
    return tag.get_text().replace('\n', ' ').strip()


def keyboard_interrupt(function):
    """Makes the decorated function to handle keyboard interrupt gracefully."""
    def _wrapper(*args, **kargs):
        try:
            function(*args, **kargs)
        except KeyboardInterrupt:
            print(_('\n[*] Operation canceled, Sayonara! :)'))
            sys.exit()
    return _wrapper


def list_downloaders(downloaders):
    """Prints the list of the given downloaders
    (:class:`~smd.downloader.Downloader`).

    :param list downloaders: a list of downloaders.
    """
    print(_("Supported sites ({}):").format(len(downloaders)))
    for downloader in downloaders:
        print(" * {} ({})".format(downloader, downloader.lang))


def mkdir(dirname, basename):
    """Tries to create a new folder ``basename`` in the folder ``dirname``
    if the name of the new folder is invalid or already exists ask the
    user to enter a new one.

    :param str dirname: the parent directory of the new folder.
    :param str basename: the name of the folder.
    :return: the path of the new created folder.
    :rtype: str
    """
    while True:
        path = pjoin(dirname, basename)
        if pexists(path):
            print(_("ERROR - Can't create folder: '{}' already exists.")
                  .format(basename))
        else:
            try:
                os.mkdir(path)
                break
            except FileNotFoundError:
                print(_("ERROR - Can't create folder '{}': Invalid name.")
                      .format(basename))
        basename = input(_("Enter a new folder name:"))
    return path


def resume(downloaders, mangas):
    """Resumes a previously canceled manga download.

    :param downloaders: the supported downloaders.
    :type downloaders: list of :class:`~smd.downloader.Downloader`
    :param mangas: a list of paths to manga folders or a path to a folder
                   where the manga folders are stored.
    """
    if isinstance(mangas, str):
        path = mangas
        mangas = []
        for manga in get_mangas(path):
            for chap in manga.chapters_iter():
                if chap['current'] != len(chap['images']):
                    mangas.append(manga)
                    break
        if len(mangas) == 0:
            die(_("No canceled download found in '{}'.").format(path))
        p_msg = _('Select mangas to continue downloading')
        mangas = select_manga(mangas, prompt_msg=p_msg, multiple=True)
    else:
        mangas = [Manga.from_folder(path) for path in mangas]
    for manga in mangas:
        for downl in downloaders:
            if downl.name == manga['site'].lower():
                downl.resume(manga)
                break
        else:
            die(_("ERROR - Unknow site: '{}'").format(manga['site']))


def select_chapters(chapters, selectors):
    """Selects the chapters specified in the given selectors.

    :param chapters: a list of chapters (:class:`~smd.util.Chapter`).
    :param str selectors: a string of comma-separated selectors.
    :return: a set of selected chapters.
    :rtype: set
    """
    if not selectors:
        return chapters
    selectors = selectors.split(',')
    chaps = set()
    ignored_chaps = set()
    for selector in selectors:
        ignore = False
        selector = selector.replace(' ', '')
        selec = selector[:]
        if selec.startswith('!'):
            ignore = True
            selec = selec[1:]
        if set(selec) - set('1234567890-:'):
            die(_("ERROR - Invalid chapter selector: '{}'").format(selector))
        try:
            selec = selec.split(':')
            if selec[0]:
                i = int(selec[0])
                if i > 0:
                    selec[0] = str(i-1)
            selec = ':'.join(selec)
            selec_chaps = eval("chapters[{}]".format(selec))
            if isinstance(selec_chaps, list):
                if not selec_chaps:
                    die(_("ERROR - Selector '{}' did not selected any "
                          "chapters.").format(selector))
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
            die(_("ERROR - Invalid chapter selector: '{}'").format(selector))
        except IndexError:
            die(_("ERROR - Chapter selector out of range: '{}'")
                .format(selector))
    if not chaps:
        chaps = set(chapters)
    return chaps - ignored_chaps


def select_downloader(downloaders):
    """Lets the user choose one downloader from the give list, keeps asking if
    the user enters invalid option.

    :param downloaders: a list of downloaders
                        (:class:`~smd.downloader.Downloader`).
    :return: the selected downloader.
    :rtype: :class:`~smd.downloader.Downloader`
    """
    print(_('Supported sites:'))
    dcount = len(str(len(downloaders)))
    for i, downl in enumerate(downloaders, 1):
        print("{}. {} ({})".format(str(i).rjust(dcount),
                                   downl.name, downl.lang))
    while True:
        try:
            i = int(input(_("Choose a site [1-{}]:")
                          .format(len(downloaders)))) - 1
            if 0 <= i < len(downloaders):
                break
        except ValueError:
            pass
        print(_("Invalid selection. Try again."))
    return downloaders[i]


def select_lang(langs):
    """Lets the user select a language from the given list, keeps asking if
    the user enters invalid option.

    :param list langs: the list of languages.
    :return: the selected language.
    """
    print(_('Available languages:'))
    dcount = len(str(len(langs)))
    for i, lang in enumerate(langs, 1):
        print("{}. {}".format(str(i).rjust(dcount), lang))
    while True:
        try:
            i = int(input(_("Choose a language [1-{}]:")
                          .format(len(langs)))) - 1
            if i >= 0 and i < len(langs):
                break
        except ValueError:
            pass
        print(_("Invalid selection. Try again."))
    return langs[i]


def select_manga(mangas, list_header='Found:', prompt_msg='Select a manga',
                 multiple=False):
    """Lets the user select a manga from the given list, keeps asking if
    the user enters invalid option numbers.

    :param mangas: a list containing the manga (:class:`~smd.util.Manga`)
                   choices.
    :param str list_header: the header message to show on top of the list.
    :param str prompt_msg: the message prompt.
    :param bool multiple: if ``True`` allows to select multiple choices.
    :return: the selected manga (or mangas).
    :rtype: :class:`~smd.util.Manga` or list of :class:`~smd.util.Manga`
    """
    print(list_header)
    if multiple:
        mangas.append(_('[SELECT ALL]'))
    dcount = len(str(len(mangas)))
    for i, manga in enumerate(mangas, 1):
        print("{}. {}".format(str(i).rjust(dcount), manga))
    while True:
        try:
            selec = input(prompt_msg+" [1-{}]:".format(len(mangas)))
            if ',' in selec:
                selec = selec.split(',')
            else:
                selec = selec.split()
            selec = [int(s) for s in selec]
            if multiple:
                if len(mangas) in selec:
                    return mangas
                else:
                    return [m for i, m in enumerate(mangas, 1) if i in selec]
            elif len(selec) == 1 and selec[0] > 0 and selec[0] <= len(mangas):
                    return mangas[selec[0]-1]
        except ValueError:
            print(_("ERROR - Invalid selection. Try again."))


def set_site(site, downloaders):
    """Sets the downloader of the given site as the preferred.

    :param str site: the site name (same as ``smd.downloader.Downloader.name``)
    :param downloaders: the list of supported downloaders
                        (:class:`~smd.downloader.Downloader`).
    """
    if site is not None:
        site = site.lower()
        for downl in downloaders:
            if downl.name == site:
                downloader = downl
                break
        else:
            print(_("ERROR - Unknow site: '{}'").format(site))
            downloader = select_downloader(downloaders)
    else:
        downloader = select_downloader(downloaders)
    downloaders.remove(downloader)
    downloaders.insert(0, downloader)


def update(downloaders, mangas):
    """Updates a previously downloaded manga.

    :param downloaders: the supported downloaders.
    :type downloaders: list of :class:`~smd.downloader.Downloader`
    :param mangas: a list of paths to manga folders or a path to a folder
                   where the manga folders are stored.
    """
    if isinstance(mangas, str):
        path = mangas
        mangas = get_mangas(path)
        if len(mangas) == 0:
            die(_("ERROR - No manga found in '{}'.").format(path))
        mangas = select_manga(mangas, prompt_msg=_('Select mangas to update'),
                              multiple=True)
    else:
        mangas = [Manga.from_folder(path) for path in mangas]
    for manga in mangas:
        for downl in downloaders:
            if downl.name == manga['site'].lower():
                downl.update(manga)
                break
        else:
            die(_("ERROR - Unknow site: '{}'").format(manga['site']))
