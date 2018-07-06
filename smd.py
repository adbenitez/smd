#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
smd --- Simple Manga Downloader.
Copyright (c) 2017-2018 Asiel Diaz Benitez.

smd is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For more information see <http://www.gnu.org/licenses/>.
'''
from abc import ABC, abstractmethod
import argparse
import http.cookiejar
import imghdr
import json
import logging
import os
import re
import sys
import urllib.request
import urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, 'libs'))

from bs4 import BeautifulSoup


USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux i686 on x86_64; '\
             'rv:60.0) Gecko/20100101 Firefox/60.0'


class Downloader(ABC):
    """
    Abstract class base of all manga downloaders
    """
    logfile = os.path.join(ROOT, 'smd.log')
    verbose = False

    def __init__(self, name, lang, site_url):
        self.name = name
        self.lang = lang
        self.site_url = site_url
        cookie_jar = http.cookiejar.MozillaCookieJar()
        # cookie_jar.load('cookies.txt')
        self.url_opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cookie_jar))
        self.url_opener.addheaders = [
            ('Host', self.site_url),
            ('Referer', self.site_url),
            ('User-Agent', USER_AGENT),
            ('Accept', 'application/json, text/plain, */*'),
            ('Accept-Language', 'en-US,en;q=0.5'),
            #('X-Requested-With', 'XMLHttpRequest')
            #('Cache-mode', 'no-cache'),
            ('DNT', '1'),  # Do Not Track
        ]
        self._init_logger()

    def __str__(self):
        return self.name

    @abstractmethod
    def search(self, manga):
        pass

    @abstractmethod
    def _download(self, manga_dir, manga, url, start, stop):
        pass

    def download(self, manga, start=0, stop=None):
        success = True
        try:
            self.logger.info("Searching for '%s' ...", manga)
            mangas = self.search(manga)
            if mangas:
                manga, url = Downloader._select_manga(mangas)
            else:
                return False
            manga_dir = os.path.abspath(manga)
            self.mkdir(manga_dir)  # TODO: avoid invalid path characters
            self._download(manga_dir, manga, url, start, stop)
        except KeyboardInterrupt as ex:
            raise ex
        except Exception as ex:
            # exec_type, exc_obj, exc_tb = sys.exc_info()
            self.logger.exception(ex)
            success = False
        if not success:
            try:
                os.rmdir(manga_dir)  # remove if empty
            except:
                pass
        return success

    def get_json(self, url):
        return json.loads(self.get(url))

    def download_img(self, url, name):
        img = self.get(url, False)
        ext = imghdr.what("", h=img)
        ext = '' if ext is None else '.'+ext
        with open(name+ext, 'bw') as outf:
            outf.write(img)

    def get(self, url, decode=True):
        while True:
            try:
                self.logger.debug('Downloading: %s', url)
                with self.url_opener.open(url) as resp:
                    if decode:
                        return resp.read().decode(errors='ignore')
                    else:
                        return resp.read()
            except ConnectionResetError as err:
                self.logger.debug(err)

    def _init_logger(self):
        self.logger = logging.getLogger(self.name)
        self.logger.parent = None
        # logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(Downloader.logfile)
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        if Downloader.verbose:
            ch.setLevel(logging.DEBUG)
        else:
            ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - '
                                      '%(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        formatter = logging.Formatter('[%(name)s] - '
                                      '%(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    @staticmethod
    def _select_manga(mangas):
        count = len(mangas)
        if count == 1:
            return mangas[0]
        print("Found:")
        for i, manga in enumerate(mangas, 1):
            print("%s. %s" % (i, manga[0]))
        i = int(input("Select manga to download [1-%s]:" % count))
        return mangas[i-1]

    @staticmethod
    def mkdir(path):
        if os.path.exists(path):
            if not os.path.isdir(path):
                raise Exception("Can't create directory,"
                                " file '%s' already exist." % path)
        else:
            os.mkdir(path)

    @staticmethod
    def gen_name(img_numb, img_count):
        zeros = len(str(img_count)) - len(str(img_numb))
        return '%s%i' % ('0'*zeros, img_numb)  # ex. 001

    @staticmethod
    def get_text(tag):
        return tag.get_text().replace('\n', ' ').strip()


class NineManga(Downloader):
    """
    Downloads manga from *.ninemanga.com
    """
    def __init__(self, site):
        lang = 'pt' if site == 'br' else site
        Downloader.__init__(self, 'ninemanga-'+site, lang,
                            'http://%s.ninemanga.com' % site)

    def search(self, manga):
        url = "%s/search/?wd=%s" % (self.site_url,
                                    urllib.parse.quote_plus(manga))
        soup = BeautifulSoup(self.get(url), 'html.parser')
        direlist = soup.find('ul', class_='direlist')
        results = [(self.get_text(a), a['href'])
                   for a in direlist.find_all('a', class_='bookname')]
        pagelist = soup.find('ul', class_='pagelist')
        if pagelist:
            # this get only first few pages:
            for page in pagelist.find_all('a')[1:-1]:
                soup = BeautifulSoup(self.get(page['href']), 'html.parser')
                direlist = soup.find('ul', class_='direlist')
                for a in direlist.find_all('a', class_='bookname'):
                    results.append((self.get_text(a), a['href']))
        return results

    def _download(self, manga_dir, manga, url, start, stop):
        self.logger.info("Getting chapters list of '%s' ...", manga)
        soup = BeautifulSoup(self.get(url), 'html.parser')
        tag = soup.find('div', class_='warning')
        if tag:
            soup = BeautifulSoup(self.get(tag.a['href']), 'html.parser')
        tag = soup.find('div', class_='silde')
        chapters = [(a['title'], a['href'])
                    for a in tag.find_all('a', class_='chapter_list_a')]
        self.logger.info("Found %i chapters for '%s'", len(chapters), manga)
        chapters.reverse()
        self.logger.info("Downloading '%s' [%i-%i]:",
                         manga, start+1, len(chapters) if stop is None else stop)
        for chap_title, url in chapters[start:stop]:
            chap_dir = os.path.join(manga_dir, chap_title)
            self.mkdir(chap_dir)
            soup = BeautifulSoup(self.get(url), 'html.parser')
            tag = soup.find('select', id='page')
            img_pages = [self.site_url + opt['value']
                         for opt in tag.find_all('option')]
            img_count = len(img_pages)
            for i, url in enumerate(img_pages, 1):
                print("\r[%s] Downloading '%s' (image: %i/%i)"
                      % (self.name, chap_title, i, img_count), end='')
                soup = BeautifulSoup(self.get(url), 'html.parser')
                url = soup.find('img', class_='manga_pic')['src']
                name = os.path.join(chap_dir, self.gen_name(i, img_count))
                self.download_img(url, name)
            if img_count > 0:
                print()


class HeavenManga(Downloader):
    """
    Downloads manga from heavenmanga.com
    """
    def __init__(self):
        Downloader.__init__(self, 'heavenmanga', 'es',
                            'http://heavenmanga.com')

    def search(self, manga):
        url = '%s/buscar/%s.html' % (self.site_url,
                                     urllib.parse.quote_plus(manga))
        # page restriction: len(manga) must to be >= 4
        soup = BeautifulSoup(self.get(url), 'html.parser')
        divs = soup.find_all('div', class_='cont_manga')
        return [(self.get_text(div.a.header), div.a['href'])
                for div in divs]

    def _download(self, manga_dir, manga, url, start, stop):
        self.logger.info("Getting chapters list of '%s' ...", manga)
        soup = BeautifulSoup(self.get(url), 'html.parser')
        chapters = [(a['title'], a['href'])
                    for a in soup.find('ul', id='holder').find_all('a')]
        self.logger.info("Found %i chapters for '%s'", len(chapters), manga)
        chapters.reverse()
        self.logger.info("Downloading '%s' [%i-%i]:",
                         manga, start+1, len(chapters) if stop is None else stop)
        for chap_title, url in chapters[start:stop]:
            chap_dir = os.path.join(manga_dir, chap_title)
            self.mkdir(chap_dir)
            soup = BeautifulSoup(self.get(url), 'html.parser')
            url = soup.find('a', id='l')['href']
            soup = BeautifulSoup(self.get(url), 'html.parser')
            img_pages = [opt['value']
                         for opt in soup.find('select').find_all('option')]
            img_count = len(img_pages)
            for i, url in enumerate(img_pages, 1):
                print("\r[%s] Downloading '%s' (image: %i/%i)"
                      % (self.name, chap_title, i, img_count), end="")
                soup = BeautifulSoup(self.get(url), 'html.parser')
                url = soup.find('img', id='p')['src']
                name = os.path.join(chap_dir, self.gen_name(i, img_count))
                self.download_img(url, name)
            if img_count > 0:
                print()


class MangaReader(Downloader):
    """
    Downloads manga from www.mangareader.net
    """
    def __init__(self):
        Downloader.__init__(self, 'mangareader', 'en',
                            'http://www.mangareader.net')

    def search(self, manga):
        url = '%s/actions/search/?q=%s&limit=100'
        url = url % (self.site_url, urllib.parse.quote_plus(manga))
        results = []
        for line in self.get(url).splitlines():
            line = line.split('|')
            if len(line) != 6:
                self.logger.warning("unknow line format: %s", '|'.join(line))
                continue
            results.append((line[2], self.site_url+line[-2]))
        return results

    def _download(self, manga_dir, manga, url, start, stop):
        self.logger.info("Getting chapters list of '%s' ...", manga)
        soup = BeautifulSoup(self.get(url), 'html.parser')
        chapters = [(self.get_text(a), self.site_url + a['href'])
                    for a in soup.find('table', id='listing').find_all('a')]
        self.logger.info("Found %i chapters for '%s'", len(chapters), manga)
        # don't need to use `chapters.reverse()` here
        self.logger.info("Downloading '%s' [%i-%i]:",
                         manga, start+1, len(chapters) if stop is None else stop)
        for chap_title, url in chapters[start:stop]:
            chap_dir = os.path.join(manga_dir, chap_title)
            self.mkdir(chap_dir)
            soup = BeautifulSoup(self.get(url), 'html.parser')
            tag = soup.find('select', id='pageMenu')
            img_pages = [self.site_url + opt['value']
                         for opt in tag.find_all('option')]
            img_count = len(img_pages)
            for i, url in enumerate(img_pages, 1):
                print("\r[%s] Downloading '%s' (image: %i/%i)"
                      % (self.name, chap_title, i, img_count), end="")
                soup = BeautifulSoup(self.get(url), 'html.parser')
                url = soup.find('img', id='img')['src']
                name = os.path.join(chap_dir, self.gen_name(i, img_count))
                self.download_img(url, name)
            if img_count > 0:
                print()


class MangaAll(Downloader):
    """
    Downloads manga from mangaall.net
    """
    def __init__(self):
        Downloader.__init__(self, 'mangaall', 'en', 'http://mangaall.net')
        self.regex = re.compile(r"var _page_total = '(?P<total>[0-9]+)';")

    def search(self, manga):
        url = '%s/search?q=%s' % (self.site_url,
                                  urllib.parse.quote_plus(manga))
        soup = BeautifulSoup(self.get(url), 'html.parser')
        divs = soup.find_all('div', class_='mainpage-manga')
        results = []
        for div in divs:
            a = div.find('div', 'media-body').a
            results.append((a['title'], a['href']))
        # TODO: get other results pages
        return results

    def _download(self, manga_dir, manga, url, start, stop):
        self.logger.info("Getting chapters list of '%s' ...", manga)
        soup = BeautifulSoup(self.get(url), 'html.parser')
        chapters = [(a['title'], a['href'])
                    for a in soup.find('section', id='examples').find_all('a')]
        self.logger.info("Found %i chapters for '%s'", len(chapters), manga)
        chapters.reverse()
        self.logger.info("Downloading '%s' [%i-%i]:",
                         manga, start+1, len(chapters) if stop is None else stop)
        for chap_title, url in chapters[start:stop]:
            chap_dir = os.path.join(manga_dir, chap_title)
            self.mkdir(chap_dir)
            img_pages = None
            soup = BeautifulSoup(self.get(url), 'html.parser')
            for script in soup.find_all('script'):
                matches = [int(n) for n in self.regex.findall(str(script.string))]
                if matches:
                    img_pages = [url+'?page='+str(n)
                                 for n in range(1, matches[-1]+1)]
                    break
            img_count = len(img_pages)
            for i, url in enumerate(img_pages, 1):
                print("\r[%s] Downloading '%s' (image: %i/%i)"
                      % (self.name, chap_title, i, img_count), end='')
                soup = BeautifulSoup(self.get(url), 'html.parser')
                url = soup.find('div', class_='each-page').img['src']
                name = os.path.join(chap_dir, self.gen_name(i, img_count))
                self.download_img(url, name)
            if img_count > 0:
                print()


class MangaDoor(Downloader):
    """
    Downloads manga from mangadoor.com
    """
    def __init__(self):
        Downloader.__init__(self, 'mangadoor', 'es', 'http://mangadoor.com')

    def search(self, manga):
        url = '%s/search?query=%s' % (self.site_url,
                                      urllib.parse.quote_plus(manga))
        suggestions = self.get_json(url)['suggestions']
        results = []
        for sugg in suggestions:
            results.append((sugg['value'], self.site_url+'/manga/'+sugg['data']))
        return results

    def _download(self, manga_dir, manga, url, start, stop):
        self.logger.info("Getting chapters list of '%s' ...", manga)
        soup = BeautifulSoup(self.get(url), 'html.parser')
        chapters = [(self.get_text(a), a['href'])
                    for a in soup.find('ul', class_='chapters').find_all('a')]
        self.logger.info("Found %i chapters for '%s'", len(chapters), manga)
        chapters.reverse()
        self.logger.info("Downloading '%s' [%i-%i]:",
                         manga, start+1, len(chapters) if stop is None else stop)
        for chap_title, url in chapters[start:stop]:
            chap_dir = os.path.join(manga_dir, chap_title)
            self.mkdir(chap_dir)
            soup = BeautifulSoup(self.get(url), 'html.parser')
            opts = soup.find('select', id='page-list').find_all('option')
            img_pages = [url+'/'+opt['value'] for opt in opts]
            img_count = len(img_pages)
            for i, url in enumerate(img_pages, 1):
                print("\r[%s] Downloading '%s' (image: %i/%i)"
                      % (self.name, chap_title, i, img_count), end='')
                soup = BeautifulSoup(self.get(url), 'html.parser')
                url = soup.find('div', id='ppp').img['src']
                name = os.path.join(chap_dir, self.gen_name(i, img_count))
                self.download_img(url, name)
            if img_count > 0:
                print()


def main(argv):
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
                   ]

    class ListDowloaders(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            print("Supported sites:")
            for downloader in sorted(downloaders, key=lambda d: d.lang):
                print(" * %s (%s)" % (downloader, downloader.lang))
            sys.exit()

    class SetLanguage(argparse.Action):
        def __call__(self, parser, namespace, lang, option_string=None):
            nonlocal downloaders
            downloaders = [d for d in downloaders if d.lang == lang]

    def download(downloaders, manga, args):
        downloader = downloaders.pop(0)
        if not downloader.download(manga, args.start, args.stop):
            downloader.logger.warning("Download have failed :(")
            if args.tryall and downloaders:
                download(downloaders, manga, args)

    parser = argparse.ArgumentParser(description="Simple Manga Downloader",
                                     epilog="Mail bug reports and suggestions "
                                     "to <asieldbenitez@gmail.com>")
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s 1.0')
    parser.add_argument("-l", "--list",
                        help="show a list of supported sites and exit",
                        nargs=0, action=ListDowloaders)
    parser.add_argument("--try",
                        help="try to download manga from other sites if "
                        "the selected site have failed, when used with "
                        "option --lang, only try sites with the selected "
                        "language",
                        dest="tryall", action="store_true")
    parser.add_argument("-f", "--file",
                        help="use a file as input for mangas to download, the "
                        "file must have a list of manga names one by line",
                        nargs='?', type=argparse.FileType('r'),
                        const=sys.stdin)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-s", "--site",
                       help="the site from which to download",
                       metavar="SITE",
                       choices=[d.name for d in downloaders])
    group.add_argument("--lang",
                       help="download from a site of the selected language "
                       "(possible values: %(choices)s)",
                       metavar="LANG",
                       choices=set(d.lang for d in downloaders),
                       action=SetLanguage)
    parser.add_argument("--start",
                        help="download starting from the given chapter",
                        type=int, default=1)
    parser.add_argument("--stop",
                        help="download up to the given chapter",
                        type=int)
    parser.add_argument("mangas",
                        help="the name of the manga to be downloaded",
                        metavar="MANGA", nargs="*")
    args = parser.parse_args(argv)

    if args.file:
        args.mangas = []
        for manga in args.file.readlines():
            manga = manga.replace('\n', '').replace('-', ' ').split()
            manga = ' '.join([word.capitalize() for word in manga
                              if word and manga[0] != '#'])
            if manga:
                args.mangas.append(manga)
    if not args.mangas:
        parser.print_usage()
    args.start -= 1
    for downl in downloaders:
        if downl.name == args.site:
            downloaders.remove(downl)
            downloaders.insert(0, downl)
            break
    for manga in args.mangas:
        download(downloaders.copy(), manga, args)


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print('\n[*] Operation canceled, Sayonara! :)')
