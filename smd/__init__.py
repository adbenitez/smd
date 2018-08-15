# -*- coding: utf-8 -*-
"""
.. module:: smd

:abbr:`smd (Simple Manga Downloader)` is a tool to search and download manga
from online manga reading web sites.

.. moduleauthor:: Asiel Díaz Benítez <asieldbenitez@gmail.com>

"""
__author__ = 'adbenitez'
__version__ = '1.6.2b'

import argparse
import gettext
import os
import sys
import typing

from smd.downloader import Downloader, get_downloaders
from smd.utils import die

if typing.TYPE_CHECKING:
    from typing import Callable, List, TypeVar, Union
    import smd
    NoReturn = TypeVar('NoReturn')

    def _(msg: str) -> str:
        return msg


CONF_DIR = os.path.join(os.path.expanduser('~'), 'smd')


def keyboard_interrupt(function: 'Callable') -> 'Callable':
    """Makes the decorated function to handle keyboard interrupt gracefully."""
    def _wrapper(*args, **kargs):
        try:
            function(*args, **kargs)
        except KeyboardInterrupt:
            print(_('\n[*] Operation canceled, Sayonara! :)'))
            sys.exit()
    return _wrapper


def create_config_folder() -> None:
    """Creates the application is configuration folder, if it doesn't exists."""
    if not os.path.isdir(CONF_DIR):
        try:
            os.mkdir(CONF_DIR)
        except (FileNotFoundError, FileExistsError):
            utils.die(_(
                "[*] CRITICAL ERROR - Can't create configuration folder '{}'.")
                .format(CONF_DIR))


def download(downloaders: 'List[smd.downloader.Downloader]', manga: str,
             chapter_selectors: str, tryall: bool) -> bool:
    """Downloads the given manga using one of the given downloaders.

    :param downloaders: the list of downloaders.
    :param manga: the manga name.
    :param chapter_selectors: the comma-separated list of chapters to download.
    :param tryall: when ``True`` if a downloader fail, then tries other
                   downloaders.
    :return: ``True`` if the download succeeded, ``False`` otherwise.
    """
    downloader = downloaders.pop(0)
    if downloader.download(manga, chapter_selectors):
        return True
    else:
        downloader.logger.error(_("Download have failed :("))
        if tryall and downloaders:
            downl = select_downloader(downloaders)
            downloaders.remove(downl)
            downloaders.insert(0, downl)
            return download(downloaders, manga, chapter_selectors, tryall)
        else:
            return False


def filter_downloaders(lang: str, downloaders: 'List[smd.downloader.Downloader]') -> 'List[smd.downloader.Downloader]':
    """Selects from the given list, the downloaders with the given language.

    :param lang: the language of the downloaders to select.
    :param downloaders: a list of downloaders.
    :return: a list of downloaders with the given language.
    """
    if not lang:
        return downloaders
    lang = lang.lower()
    langs = sorted(set(d.lang for d in downloaders))
    if lang not in langs:
        print(_("[*] ERROR - Unknow language: '{}'").format(lang))
        lang = select_lang(langs)
    return [d for d in downloaders if d.lang == lang]


def get_args_parser() -> argparse.ArgumentParser:
    """Creates an arguments parser for the program is command line interface.

    :param version: the application is version number.
    :return: the arguments parser.
    """
    epilog = _("Mail bug reports and suggestions to "
               "<asieldbenitez@gmail.com>. Support this tool at "

               "http://liberapay.com/adbenitez, thanks!")
    parser = argparse.ArgumentParser(description=_("Simple Manga Downloader"),
                                     epilog=epilog)
    hmsg = _("show program's version number and exit")
    parser.add_argument('-v', '--version', help=hmsg, action='version',
                        version='%(prog)s ' + __version__)
    hmsg = _('shows program is copyright notice')
    parser.add_argument('--license', help=hmsg, action='store_true')
    hmsg = _('makes the program more verbose')
    parser.add_argument('--verbose', help=hmsg, action='store_true')
    hmsg = _("show a list of supported sites and exit")
    parser.add_argument("-l", "--list", help=hmsg, dest="list_sites",
                        action="store_true")
    hmsg = _("try to download manga from other sites if the selected site have"
             " failed, when used with option --lang, only try sites with the "
             "selected language")
    parser.add_argument("--tryall", help=hmsg, action="store_true")
    hmsg = _("use a file as input for mangas to download, the file must have a"
             " list of manga names one by line")
    parser.add_argument("-f", "--file", help=hmsg, nargs='?', const=sys.stdin,
                        type=argparse.FileType('r'))
    group = parser.add_mutually_exclusive_group()
    hmsg = _("the site from which to download")
    group.add_argument("-s", "--site", help=hmsg, metavar="SITE")
    hmsg = _("download only from sites of the selected language")
    group.add_argument("--lang", help=hmsg, metavar="LANG")
    hmsg = _("download only the given chapters, when not used all chapters are"
             " downloaded. Valid selectors are: chapter numbers (e.g. 2,15,20)"
             ", ranges (e.g. 1:10, 30:, :20), negative numbers which mean the "
             "chapter number in reverse order (e.g. -1 means the last chapter)"
             " and to ignore chapters instead of download them use '!' in "
             "front of any of the previous selectors (e.g. !5, !2:20, !-2). "
             "You can use multiple selectors separating them with a comma "
             "(e.g. '5,10,20:30,-1')")
    parser.add_argument("--chapters", help=hmsg)
    hmsg = _("the directory to use to save the mangas, by default the working "
             "directory is used")
    parser.add_argument("-d", "--directory", help=hmsg)
    hmsg = _("searches for new chapters of the given mangas")
    parser.add_argument("-u", "--update", help=hmsg, action='store_true')
    hmsg = _("continues the canceled download of the given mangas")
    parser.add_argument("-c", "--continue", help=hmsg, dest='resume',
                        action='store_true')
    hmsg = _("the name (or partial name) of the manga to search and download, "
             "or paths to manga folders when used with `-u` or `-c` options")
    parser.add_argument("mangas", help=hmsg, metavar="MANGA", nargs="*")
    return parser


def list_downloaders(downloaders: 'List[smd.downloader.Downloader]') -> None:
    """Prints the list of the given downloaders.

    :param downloaders: a list of downloaders.
    """
    print(_("Supported sites ({}):").format(len(downloaders)))
    for downloader in downloaders:
        print(" * {} ({})".format(downloader, downloader.lang))


def resume(downloaders: 'List[smd.downloader.Downloader]',
           mangas: 'Union[List[str], str]') -> None:
    """Resumes a previously canceled manga download.

    :param downloaders: the supported downloaders.
     :param mangas: a list of paths to manga folders or a path to a folder
                    where the manga folders are stored.
    """
    mangalist = []  # type: List[smd.utils.Manga]
    if isinstance(mangas, str):
        for manga in utils.get_mangas(mangas):
            for chap in manga.chapters():
                if chap.current != len(chap.images):
                    mangalist.append(manga)
                    break
        if len(mangas) == 0:
            utils.die(_("No canceled download found in '{}'.").format(mangas))
        p_msg = _('Select mangas to continue downloading')
        mangalist = utils.select_mangas(mangalist, prompt_msg=p_msg)
    else:
        mangalist = [utils.Manga.from_folder(path) for path in mangas]
    for manga in mangalist:
        for downl in downloaders:
            if downl.name == manga.site.lower():
                downl.resume(manga)
                break
        else:
            utils.die(_("[*] ERROR - Unknow site: '{}'").format(manga.site))


def select_downloader(downloaders: 'List[smd.downloader.Downloader]') -> 'smd.downloader.Downloader':
    """Lets the user choose one downloader from the give list, keeps asking if
    the user enters invalid option.

    :param downloaders: a list of downloaders.
    :return: the selected downloader.
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
        print(_("[*] ERROR - Invalid selection. Try again."))
    return downloaders[i]


def select_lang(langs: 'List[str]') -> str:
    """Lets the user select a language from the given list, keeps asking if
    the user enters invalid option.

    :param langs: the list of languages.
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
        print(_("[*] ERROR - Invalid selection. Try again."))
    return langs[i]


def set_locale(language: str, localedir: str) -> None:
    if language == 'SYSTEM':
        gettext.install('smd', localedir)
    else:
        lang = gettext.translation('smd', localedir=localedir,
                                   languages=[language], fallback=True)
        lang.install()


def set_site(site: str, downloaders: 'List[smd.downloader.Downloader]') -> None:
    """Sets the downloader of the given site as the preferred.

    :param site: the site name (same as ``smd.downloader.Downloader.name``)
    :param downloaders: the list of supported downloaders.
    """
    if site is not None:
        site = site.lower()
        for downl in downloaders:
            if downl.name == site:
                downloader = downl
                break
        else:
            print(_("[*] ERROR - Unknow site: '{}'").format(site))
            downloader = select_downloader(downloaders)
    else:
        downloader = select_downloader(downloaders)
    downloaders.remove(downloader)
    downloaders.insert(0, downloader)


def show_copyright() -> None:
    """Shows copyright notice."""
    print(_(
        "\n\tsmd --- Simple Manga Downloader.\n"
        "\tCopyright (c) 2017-2018 Asiel Díaz Benítez.\n\n"
        "\tsmd is free software: you can redistribute it and/or modify\n"
        "\tit under the terms of the GNU General Public License as published"
        " by\n"
        "\tthe Free Software Foundation, either version 3 of the License, or\n"
        "\t(at your option) any later version.\n\n"
        "\tsmd is distributed in the hope that it will be useful,\n"
        "\tbut WITHOUT ANY WARRANTY; without even the implied warranty of\n"
        "\tMERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n"
        "\tGNU General Public License for more details.\n\n"
        "\tYou should have received a copy of the GNU General Public License\n"
        "\tlong with smd. If not, see <http://www.gnu.org/licenses/>.\n"))


def update(downloaders: 'List[smd.downloader.Downloader]',
           mangas: 'Union[List[str], str]') -> None:
    """Updates a previously downloaded manga.

    :param downloaders: a list of supported downloaders.
    :param mangas: a list of paths to manga folders or a path to a folder
                   where the manga folders are stored.
    """
    mangalist = []  # type: List[smd.utils.Manga]
    if isinstance(mangas, str):
        mangalist = utils.get_mangas(mangas)
        if len(mangalist) == 0:
            utils.die(_("[*] ERROR - No manga found in '{}'.").format(mangas))
        mangalist = utils.select_mangas(mangalist,
                                        prompt_msg=_('Select mangas to update'))
    else:
        mangalist = [utils.Manga.from_folder(path) for path in mangas]
    for manga in mangalist:
        for downl in downloaders:
            if downl.name == manga.site.lower():
                downl.update(manga)
                break
        else:
            utils.die(_("[*] ERROR - Unknow site: '{}'").format(manga.site))


@keyboard_interrupt
def main(cmd_args: 'List[str]' = sys.argv[1:]) -> 'NoReturn':
    """Executes the command line interface of smd."""
    create_config_folder()
    config = utils.Config(os.path.join(CONF_DIR, 'smd.cfg'))
    if not config.exists():
        config.save()
    set_locale(config['language'].strip(),
               os.path.join(os.path.dirname(__file__), 'locale'))
    argparse._ = _  # type: ignore
    args = get_args_parser().parse_args(cmd_args)
    Downloader.logfile = os.path.join(CONF_DIR, __name__+'.log')
    Downloader.verbose = args.verbose
    downloaders = filter_downloaders(args.lang, get_downloaders())
    downloaders.sort(key=lambda d: d.lang)
    failed = 0
    if args.file:
        args.mangas = [m.strip() for m in args.file.readlines()
                       if m and m[0] != '#']
    if args.directory:
        os.chdir(args.directory)
    else:
        os.chdir(config['manga_dir'])
    if args.license:
        show_copyright()
    elif args.list_sites:
        list_downloaders(downloaders)
    elif args.resume:
        if args.mangas:
            resume(downloaders, args.mangas)
        else:
            resume(downloaders, args.directory)
    elif args.update:
        if args.mangas:
            update(downloaders, args.mangas)
        else:
            update(downloaders, args.directory)
    else:
        set_site(args.site, downloaders)
        if not args.mangas:
            args.mangas = [input(_("Enter manga name or text to search:"))]
        for manga in args.mangas:
            if not download(downloaders[:], manga, args.chapters,
                            args.tryall):
                failed += 1
    sys.exit(failed)
