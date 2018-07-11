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
__version__ = '1.4.0'

import argparse
import sys

from .downloader import (NineManga, HeavenManga, MangaReader, MangaAll,
                         MangaDoor, MangaNelo, MangaHere)

# ROOT = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(0, os.path.join(ROOT, 'libs'))


class ShowCopyright(argparse.Action):
    '''Shows copyright notice'''
    def __call__(self, parser, namespace, values, option_string=None):
        print(
            "smd --- Simple Manga Downloader.\n"
            "Copyright (c) 2017-2018 Asiel Díaz Benítez.\n\n"
            "smd is free software: you can redistribute it and/or modify\n"
            "it under the terms of the GNU General Public License as published by\n"
            "the Free Software Foundation, either version 3 of the License, or\n"
            "(at your option) any later version.\n\n"
            "smd is distributed in the hope that it will be useful,\n"
            "but WITHOUT ANY WARRANTY; without even the implied warranty of\n"
            "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n"
            "GNU General Public License for more details.\n\n"
            "You should have received a copy of the GNU General Public License\n"
            "along with smd. If not, see <http://www.gnu.org/licenses/>.")
        sys.exit()


def keyboard_interrupt(function):
    '''Makes the decorated function to handle keyboard interrupt gracefully'''
    def wrapper(*args, **kargs):
        try:
            function(*args, **kargs)
        except KeyboardInterrupt:
            print('\n[*] Operation canceled, Sayonara! :)')
            sys.exit(0)
    return wrapper


def select_downloader(downloaders):
    print('Supported sites:')
    dcount = len(str(len(downloaders)))
    for i, d in enumerate(downloaders, 1):
        print("%s. %s (%s)" % (str(i).rjust(dcount), d.name, d.lang))
    while True:
        try:
            i = int(input("Choose a site [1-%s]:" % len(downloaders))) - 1
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
        print("%s. %s" % (str(i).rjust(dcount), lang))
    while True:
        try:
            i = int(input("Choose a language [1-%s]:" % len(langs))) - 1
            if i >= 0 and i < len(langs):
                break
        except ValueError:
            pass
        print("Invalid selection. Try again.")
    return langs[i]


def download(downloaders, manga, args):
    downloader = downloaders.pop(0)
    if not downloader.download(manga, args.start, args.stop):
        downloader.logger.warning("Download have failed :(")
        if args.tryall and downloaders:
            select_downloader(downloaders)
            download(downloaders, manga, args)


@keyboard_interrupt
def main():
    parser = argparse.ArgumentParser(description="Simple Manga Downloader",
                                     epilog="Mail bug reports and suggestions "
                                     "to <asieldbenitez@gmail.com>")
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s '+__version__)
    parser.add_argument('--license',
                        help='shows program copyright notice',
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
                       help="download from a site of the selected language",
                       metavar="LANG")
    parser.add_argument("--start",
                        help="download starting from the given chapter "
                        "(default: %(default)s)",
                        type=int, default=1)
    parser.add_argument("--stop",
                        help="download up to the given chapter",
                        type=int)
    parser.add_argument("mangas",
                        help="the name (or partial name) of the manga to search "
                        "and download",
                        metavar="MANGA", nargs="*")
    args = parser.parse_args()

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
    args.start -= 1
    if args.start < 0:
        print("ERROR - invalid start chapter.")
        sys.exit(1)
    if args.stop and args.stop < args.start:
        print("ERROR - stop chapter must be higher than start chapter.")
        sys.exit(1)
    if args.lang:
        langs = list(set(d.lang for d in downloaders))
        if args.lang not in langs:
            print("ERROR - Unknow language: '%s'" % args.lang)
            args.lang = select_lang(langs)
        downloaders = [d for d in downloaders if d.lang == args.lang]
    if args.list_sites:
        print("Supported sites (%i):" % len(downloaders))
        for downloader in downloaders:
            print(" * %s (%s)" % (downloader, downloader.lang))
        sys.exit(0)
    if args.site is not None:
        args.site = args.site.lower()
        sites = [d.name for d in downloaders]
        if args.site not in sites:
            print("ERROR - Unknow site: '%s'" % args.site)
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
        args.mangas = []
        for manga in args.file.readlines():
            manga = manga.strip()
            if manga and manga[0] != '#':
                args.mangas.append(manga)
    if not args.mangas:
        args.mangas = [input("Enter manga name or text to search:")]
    for manga in args.mangas:
        download(downloaders.copy(), manga, args)
