# -*- coding: utf-8 -*-
'''
smd --- Simple Manga Downloader.
Copyright (c) 2017-2018 Asiel Díaz Benítez.

smd is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

smd is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with smd. If not, see <http://www.gnu.org/licenses/>.
'''
import argparse
import os
import sys

from .downloader import (Downloader, NineManga, HeavenManga, MangaReader,
                         MangaAll, MangaDoor, MangaNelo, MangaHere)

__version__ = '1.5.0'


class ShowCopyright(argparse.Action):
    '''Shows copyright notice'''
    def __call__(self, parser, namespace, values, option_string=None):
        print(
            "smd --- Simple Manga Downloader.\n"
            "Copyright (c) 2017-2018 Asiel Díaz Benítez.\n\n"
            "smd is free software: you can redistribute it and/or modify\n"
            "it under the terms of the GNU General Public License as published"
            " by\n"
            "the Free Software Foundation, either version 3 of the License,"
            " or\n(at your option) any later version.\n\n"
            "smd is distributed in the hope that it will be useful,\n"
            "but WITHOUT ANY WARRANTY; without even the implied warranty of\n"
            "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n"
            "GNU General Public License for more details.\n\n"
            "You should have received a copy of the GNU General Public"
            " License\n"
            "along with smd. If not, see <http://www.gnu.org/licenses/>.")
        sys.exit()


def keyboard_interrupt(function):
    '''Makes the decorated function to handle keyboard interrupt gracefully'''
    def wrapper(*args, **kargs):
        try:
            function(*args, **kargs)
        except KeyboardInterrupt:
            print('\n[*] Operation canceled, Sayonara! :)')
            sys.exit()
    return wrapper


def select_downloader(downloaders):
    print('Supported sites:')
    dcount = len(str(len(downloaders)))
    for i, d in enumerate(downloaders, 1):
        print("{}. {} ({})".format(str(i).rjust(dcount), d.name, d.lang))
    while True:
        try:
            i = int(input("Choose a site [1-{}]:"
                          .format(len(downloaders)))) - 1
            if i >= 0 and i < len(downloaders):
                break
        except ValueError:
            pass
        print("Invalid selection. Try again.")
    downloaders.insert(0, downloaders.pop(i))


def select_lang(langs):
    print('Available languages:')
    dcount = len(str(len(langs)))
    for i, lang in enumerate(langs, 1):
        print("{}. {}".format(str(i).rjust(dcount), lang))
    while True:
        try:
            i = int(input("Choose a language [1-{}]:".format(len(langs)))) - 1
            if i >= 0 and i < len(langs):
                break
        except ValueError:
            pass
        print("Invalid selection. Try again.")
    return langs[i]


def list_downloaders(downloaders):
    print("Supported sites ({}):".format(len(downloaders)))
    for downloader in downloaders:
        print(" * {} ({})".format(downloader, downloader.lang))


def create_config_folder():
    conf_dir = os.path.join(os.path.expanduser('~'), 'smd')
    if os.path.exists(conf_dir):
        if not os.path.isdir(conf_dir):
            print("CRITICAL ERROR - Can't create configuration folder '{}'."
                  .format(conf_dir))
            sys.exit(1)
    else:
        try:
            os.mkdir(conf_dir)
        except FileNotFoundError:
            print("CRITICAL ERROR - Can't create configuration folder '{}'."
                  .format(conf_dir))
            sys.exit(1)
    return conf_dir


def download(downloaders, manga, chapter_selectors, tryall):
    downloader = downloaders.pop(0)
    if not downloader.download(manga, chapter_selectors):
        downloader.logger.error("Download have failed :(")
        if tryall and downloaders:
            select_downloader(downloaders)
            return download(downloaders, manga, chapter_selectors, tryall)
        else:
            return False
    else:
        return True


@keyboard_interrupt
def main():
    epilog = ("Mail bug reports and suggestions to <asieldbenitez@gmail.com>. "
              "Support this tool at http://liberapay.com/adbenitez, thanks!")
    parser = argparse.ArgumentParser(description="Simple Manga Downloader",
                                     epilog=epilog)
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s '+__version__)
    parser.add_argument('--verbose',
                        help='makes the program more verbose',
                        action='store_true')
    parser.add_argument('--license',
                        help='shows program is copyright notice',
                        nargs=0,
                        action=ShowCopyright)
    parser.add_argument("-l", "--list",
                        help="show a list of supported sites and exit",
                        dest="list_sites",
                        action="store_true")
    parser.add_argument("--tryall",
                        help="try to download manga from other sites if "
                        "the selected site have failed, when used with "
                        "option --lang, only try sites with the selected "
                        "language",
                        action="store_true")
    parser.add_argument("-f", "--file",
                        help="use a file as input for mangas to download, the "
                        "file must have a list of manga names one by line",
                        nargs='?', type=argparse.FileType('r'),
                        const=sys.stdin)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-s", "--site",
                       help="the site from which to download",
                       metavar="SITE")
    group.add_argument("--lang",
                       help="download only from sites of the selected "
                       "language",
                       metavar="LANG")
    parser.add_argument("--chapters",
                        help="download only the given chapters, when not used "
                        "all chapters are downloaded. Valid selectors are: "
                        "chapter numbers (e.g. 2,15,20), ranges (e.g. 1:10, "
                        "30:, :20), negative numbers which mean the chapter "
                        "number in reverse order (e.g. -1 means the last "
                        "chapter) and to ignore chapters instead of download "
                        "them use '!' in front of any of the previous "
                        "selectors (e.g. !5, !2:20, !-2). You can use "
                        "multiple selectors separating them with a comma "
                        "(e.g. '5,10,20:30,-1')")
    parser.add_argument("-d", "--directory",
                        help="the directory to use to save the mangas, by "
                        "default the working directory is used")
    parser.add_argument("mangas",
                        help="the name (or partial name) of the manga to "
                        "search and download",
                        metavar="MANGA", nargs="*")
    args = parser.parse_args()
    conf_dir = create_config_folder()
    Downloader.logfile = os.path.join(conf_dir, 'smd.log')
    Downloader.verbose = args.verbose
    downloaders = [NineManga('en'),
                   NineManga('es'),
                   NineManga('ru'),
                   NineManga('de'),
                   NineManga('it'),
                   NineManga('br'),
                   HeavenManga(),
                   MangaReader(),
                   MangaAll(),
                   MangaDoor(),
                   MangaNelo(),
                   MangaHere()]
    downloaders.sort(key=lambda d: d.lang)
    if args.lang:
        langs = list(set(d.lang for d in downloaders))
        if args.lang not in langs:
            print("ERROR - Unknow language: '{}'".format(args.lang))
            args.lang = select_lang(langs)
        downloaders = [d for d in downloaders if d.lang == args.lang]
    if args.list_sites:
        list_downloaders(downloaders)
        sys.exit(0)
    if args.site is not None:
        args.site = args.site.lower()
        if args.site not in [d.name for d in downloaders]:
            print("ERROR - Unknow site: '{}'".format(args.site))
            select_downloader(downloaders)
        else:
            for downl in downloaders:
                if downl.name == args.site:
                    downloaders.remove(downl)
                    downloaders.insert(0, downl)
                    break
    else:
        select_downloader(downloaders)
    if args.file:
        args.mangas = [m.strip()
                       for m in args.file.readlines() if m and m[0] != '#']
    if not args.mangas:
        args.mangas = [input("Enter manga name or text to search:")]
    if args.directory:
        os.chdir(args.directory)
    failed = 0
    for manga in args.mangas:
        if not download(downloaders[:], manga, args.chapters, args.tryall):
            failed += 1
    sys.exit(failed)
