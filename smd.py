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
from http.cookiejar import MozillaCookieJar
import imghdr
import json
import logging
import os
import random
import re
import sys
from urllib.request import Request
import urllib.request
import urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, 'libs'))

try:
    from bs4 import BeautifulSoup
except:
    print("This program needs BeautifulSoup to work,",
          "to install it use the command: pip install beautifulsoup4")
    sys.exit(1)

ua_list = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux i686 on x86_64; rv:60.0) Gecko/20100101 Firefox/60.0',
]
USER_AGENT = ua_list[random.randrange(0, len(ua_list))]


class Downloader(ABC):
    """
    Abstract class base of all manga downloaders.
    """
    logfile = os.path.join(ROOT, 'smd.log')
    verbose = False

    def __init__(self, name, lang, site_url):
        self.name = name
        self.lang = lang
        self.site_url = site_url
        cookie_jar = MozillaCookieJar()
        # cookie_jar.load('cookies.txt')
        self.url_opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cookie_jar))
        self.url_opener.addheaders = [
            ('Host', self.site_url),
            ('Referer', self.site_url),
            ('User-Agent', USER_AGENT),
            ('Accept', 'application/json, text/plain, */*'),
            ('Accept-Language', 'en-US,en;q=0.5'),
            ('DNT', '1'),  # Do Not Track... they gonna track you anyway...
        ]
        self._init_logger()

    def __str__(self):
        return self.name

    @abstractmethod
    def search(self, manga):
        '''
        Receives a frase or manga title to search and returns a list of tuples
        each one with the tile and URL of the manga that matched the frase.
        '''
        pass

    @abstractmethod
    def get_chapters(self, manga_url):
        '''
        Receives the URL of a manga and returns a list of tuples each one with
        the chapter title and URL.
        '''
        pass

    @abstractmethod
    def get_images(self, chapter_url):
        '''
        Receives the chapter URL and returns the list of images for the given
        chapter, or a list of URL where the images can be found using `get_image`.
        '''
        pass

    def get_image(self, image_url):
        '''
        When `get_images` doesn't return the images URLs this method must be
        overridden to get the image URL from the given URL.
        '''
        return image_url

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
            self._mkdir(manga_dir)  # TODO: avoid invalid path characters
            self.logger.info("Getting chapters list of '%s' ...", manga)
            chapters = self.get_chapters(url)
            self.logger.info("Found %i chapters for '%s'", len(chapters), manga)
            self.logger.info("Downloading '%s' [%i-%i]:", manga, start+1,
                             len(chapters) if stop is None else stop)
            for chap_title, url in chapters[start:stop]:
                chap_dir = os.path.join(manga_dir, chap_title)
                self._mkdir(chap_dir)
                self.logger.info("Getting images list for chapter '%s' ...",
                                 chap_title)
                images = self.get_images(url)
                img_count = len(images)
                dcount = len(str(img_count))
                for i, url in enumerate(images, 1):
                    print("\r[%s] Downloading '%s' (image: %i/%i)"
                          % (self.name, chap_title, i, img_count), end='')
                    url = self.get_image(url)
                    name = os.path.join(chap_dir, str(i).zfill(dcount))
                    self.download_img(url, name)
                if img_count > 0:
                    print()
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

    def get_json(self, url, data={}, method='GET'):
        return json.loads(self.get(url, data=data, method=method, xhr=True))

    def download_img(self, url, name):
        img = self.get(url, decode=False)
        ext = imghdr.what("", h=img)
        ext = '' if ext is None else '.'+ext
        with open(name+ext, 'bw') as outf:
            outf.write(img)

    def get(self, url, data={}, method='GET', xhr=False, decode=True):
        method = method.upper()
        data = urllib.parse.urlencode(data)
        if method == 'GET':
            if data:
                url = url+'?'+data
            data = None
        elif method == 'POST':
            data = data.encode('ascii')
        else:
            raise Exception("Only GET and POST methods are implemented.")
        if xhr:
            headers = {'X-Requested-With': 'XMLHttpRequest'}
        else:
            headers = {}
        while True:
            try:
                self.logger.debug('Downloading: %s', url)
                with self.url_opener.open(Request(url, data, headers)) as resp:
                    if decode:
                        return resp.read().decode(errors='ignore')
                    else:
                        return resp.read()
            except ConnectionResetError as err:
                self.logger.debug(err)

    def _init_logger(self):
        self.logger = logging.getLogger(self.name)
        self.logger.parent = None
        fh = logging.FileHandler(Downloader.logfile, mode='w')
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
        print("Found:")
        dcount = len(str(len(mangas)))
        for i, manga in enumerate(mangas, 1):
            print("%s. %s" % (str(i).rjust(dcount), manga[0]))
        i = int(input("Select manga to download [1-%s]:" % len(mangas)))
        return mangas[i-1]

    @staticmethod
    def _mkdir(path):
        if os.path.exists(path):
            if not os.path.isdir(path):
                raise Exception("Can't create directory,"
                                " file '%s' already exist." % path)
        else:
            os.mkdir(path)

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
        url = self.site_url+"/search/"
        soup = BeautifulSoup(self.get(url, {'wd': manga}), 'html.parser')
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

    def get_chapters(self, manga_url):
        soup = BeautifulSoup(self.get(manga_url), 'html.parser')
        tag = soup.find('div', class_='warning')
        if tag:
            soup = BeautifulSoup(self.get(tag.a['href']), 'html.parser')
        tag = soup.find('div', class_='silde')
        chapters = [(a['title'], a['href'])
                    for a in tag.find_all('a', class_='chapter_list_a')]
        chapters.reverse()
        return chapters

    def get_images(self, chapter_url):
        soup = BeautifulSoup(self.get(chapter_url), 'html.parser')
        tag = soup.find('select', id='page')
        return [self.site_url + opt['value']
                for opt in tag.find_all('option')]

    def get_image(self, image_url):
        soup = BeautifulSoup(self.get(image_url), 'html.parser')
        return soup.find('img', class_='manga_pic')['src']


class HeavenManga(Downloader):
    """
    Downloads manga from heavenmanga.com
    """
    def __init__(self):
        Downloader.__init__(self, 'heavenmanga', 'es',
                            'http://heavenmanga.com')

    def search(self, manga):
        # TODO: find a better way to do this:
        url = '%s/buscar/%s.html' % (self.site_url,
                                     urllib.parse.quote_plus(manga))
        # page restriction: len(manga) must to be >= 4
        soup = BeautifulSoup(self.get(url), 'html.parser')
        divs = soup.find_all('div', class_='cont_manga')
        return [(self.get_text(div.a.header), div.a['href'])
                for div in divs]

    def get_chapters(self, manga_url):
        soup = BeautifulSoup(self.get(manga_url), 'html.parser')
        chapters = [(a['title'], a['href'])
                    for a in soup.find('ul', id='holder').find_all('a')]
        chapters.reverse()
        return chapters

    def get_images(self, chapter_url):
        soup = BeautifulSoup(self.get(chapter_url), 'html.parser')
        chapter_url = soup.find('a', id='l')['href']
        soup = BeautifulSoup(self.get(chapter_url), 'html.parser')
        return [opt['value']
                for opt in soup.find('select').find_all('option')]

    def get_image(self, image_url):
        soup = BeautifulSoup(self.get(image_url), 'html.parser')
        return soup.find('img', id='p')['src']


class MangaReader(Downloader):
    """
    Downloads manga from www.mangareader.net
    """
    def __init__(self):
        Downloader.__init__(self, 'mangareader', 'en',
                            'https://www.mangareader.net')

    def search(self, manga):
        url = self.site_url+'/actions/search/'
        results = []
        for line in self.get(url, {'q': manga, 'limit': 100}).splitlines():
            line = line.split('|')
            if len(line) != 6:
                self.logger.warning("unknow line format: %s", '|'.join(line))
                continue
            results.append((line[2], self.site_url+line[-2]))
        return results

    def get_chapters(self, manga_url):
        soup = BeautifulSoup(self.get(manga_url), 'html.parser')
        chapters = [(self.get_text(a), self.site_url + a['href'])
                    for a in soup.find('table', id='listing').find_all('a')]
        # don't need to use `chapters.reverse()` here
        return chapters

    def get_images(self, chapter_url):
        soup = BeautifulSoup(self.get(chapter_url), 'html.parser')
        tag = soup.find('select', id='pageMenu')
        return [self.site_url + opt['value']
                for opt in tag.find_all('option')]

    def get_image(self, image_url):
        soup = BeautifulSoup(self.get(image_url), 'html.parser')
        return soup.find('img', id='img')['src']


class MangaAll(Downloader):
    """
    Downloads manga from mangaall.net
    """
    def __init__(self):
        Downloader.__init__(self, 'mangaall', 'en', 'http://mangaall.net')
        self.regex = re.compile(r"var _page_total = '(?P<total>[0-9]+)';")

    def search(self, manga):
        url = self.site_url+'/search/'
        soup = BeautifulSoup(self.get(url, {'q': manga}), 'html.parser')
        divs = soup.find_all('div', class_='mainpage-manga')
        results = []
        for div in divs:
            a = div.find('div', 'media-body').a
            results.append((a['title'], a['href']))
        # TODO: get other results pages
        return results

    def get_chapters(self, manga_url):
        soup = BeautifulSoup(self.get(manga_url), 'html.parser')
        chapters = [(a['title'], a['href'])
                    for a in soup.find('section', id='examples').find_all('a')]
        chapters.reverse()
        return chapters

    def get_images(self, chapter_url):
        soup = BeautifulSoup(self.get(chapter_url), 'html.parser')
        for script in soup.find_all('script'):
            matches = [int(n) for n in self.regex.findall(str(script.string))]
            if matches:
                return [chapter_url+'?page='+str(n)
                        for n in range(1, matches[-1]+1)]
        raise Exception("Can't find images list")

    def get_image(self, image_url):
        soup = BeautifulSoup(self.get(image_url), 'html.parser')
        return soup.find('div', class_='each-page').img['src']


class MangaDoor(Downloader):
    """
    Downloads manga from mangadoor.com
    """
    def __init__(self):
        Downloader.__init__(self, 'mangadoor', 'es', 'http://mangadoor.com')

    def search(self, manga):
        url = self.site_url+'/search/'
        suggestions = self.get_json(url, {'query': manga})['suggestions']
        results = []
        for sugg in suggestions:
            results.append((sugg['value'], self.site_url+'/manga/'+sugg['data']))
        return results

    def get_chapters(self, manga_url):
        soup = BeautifulSoup(self.get(manga_url), 'html.parser')
        chapters = [(self.get_text(a), a['href'])
                    for a in soup.find('ul', class_='chapters').find_all('a')]
        chapters.reverse()
        return chapters

    def get_images(self, chapter_url):
        soup = BeautifulSoup(self.get(chapter_url), 'html.parser')
        opts = soup.find('select', id='page-list').find_all('option')
        return [chapter_url+'/'+opt['value'] for opt in opts]

    def get_image(self, image_url):
        soup = BeautifulSoup(self.get(image_url), 'html.parser')
        return soup.find('div', id='ppp').img['src']


class MangaNelo(Downloader):
    '''
    Downloads manga from manganelo.com
    '''
    def __init__(self):
        Downloader.__init__(self, 'manganelo', 'en', 'https://manganelo.com')

    def search(self, manga):
        query_str = ''
        for char in manga:
            if char.isalnum():
                query_str += char
            else:
                query_str += ' '
        query_str = '_'.join(query_str.split())
        data = {'search_style': 'tentruyen', 'searchword': query_str}
        url = self.site_url+'/home_json_search/'
        data = self.get_json(url, data, method='POST')
        results = []
        for result in data:
            name = self.get_text(BeautifulSoup(result['name'], 'html.parser'))
            url = self.site_url+'/manga/'+result['nameunsigned']
            results.append((name, url))
        return results

    def get_chapters(self, manga_url):
        soup = BeautifulSoup(self.get(manga_url), 'html.parser')
        div = soup.find('div', class_='chapter-list')
        chapters = []
        for a in div.find_all('a'):
            if a['href'].startswith('/'):
                a['href'] = 'https:'+a['href']
            chapters.append((self.get_text(a), a['href']))
        chapters.reverse()
        return chapters

    def get_images(self, chapter_url):
        soup = BeautifulSoup(self.get(chapter_url), 'html.parser')
        div = soup.find('div', id='vungdoc')
        return [img['src'] for img in div.find_all('img')]


class MangaHere(Downloader):
    """
    Downloads manga from www.mangahere.cc
    """
    def __init__(self):
        Downloader.__init__(self, 'mangahere', 'en', 'http://www.mangahere.cc')

    def search(self, manga):
        url = self.site_url+'/ajax/search.php'
        json = self.get_json(url, {'query': manga})
        results = []
        for title, url in zip(json['suggestions'], json['data']):
            results.append((title, 'http:'+url))
        return results

    def get_chapters(self, manga_url):
        soup = BeautifulSoup(self.get(manga_url), 'html.parser')
        ul = soup.find('div', class_='detail_list').ul
        chapters = [(self.get_text(a), 'http:'+a['href'])
                    for a in ul.find_all('a')]
        chapters.reverse()
        return chapters

    def get_images(self, chapter_url):
        soup = BeautifulSoup(self.get(chapter_url), 'html.parser')
        opts = soup.find('select', class_='wid60').find_all('option')
        return ['http:'+opt['value']
                for opt in opts if self.get_text(opt) != 'Featured']

    def get_image(self, image_url):
        soup = BeautifulSoup(self.get(image_url), 'html.parser')
        return soup.find('img', id='image')['src']


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
                   MangaNelo(),
                   MangaHere()]
    downloaders.sort(key=lambda d: d.lang)

    class ListDowloaders(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            print("Supported sites (%i):" % len(downloaders))
            for downloader in downloaders:
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

    def select_downloader():
        print('Supported sites:')
        dcount = len(str(len(downloaders)))
        for i, d in enumerate(downloaders, 1):
            print("%s. %s (%s)" % (str(i).rjust(dcount), d.name, d.lang))
        i = int(input("Choose a site [1-%s]:" % len(downloaders)))
        downloaders.insert(0, downloaders.pop(i-1))

    parser = argparse.ArgumentParser(description="Simple Manga Downloader",
                                     epilog="Mail bug reports and suggestions "
                                     "to <asieldbenitez@gmail.com>")
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s 1.3')
    parser.add_argument('--license',
                        help='shows program copyright notice')
    parser.add_argument("-l", "--list",
                        help="show a list of supported sites and exit",
                        nargs=0, action=ListDowloaders)
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
    if args.site is not None:
        for d in downloaders:
            if d.name == args.site.lower():
                downloaders.remove(d)
                downloaders.insert(0, d)
                break
        else:
            print("ERROR - Unknow site: '%s'" % args.site)
            select_downloader()
    else:
        select_downloader()
    for manga in args.mangas:
        download(downloaders.copy(), manga, args)


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print('\n[*] Operation canceled, Sayonara! :)')
