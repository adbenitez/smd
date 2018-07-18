# -*- coding: utf-8 -*-
# Use of this source code is governed by GPL3 license that can be
# found in the LICENSE file.
'''
This module provides the downloaders able to grab content from the
supported sites
'''

from abc import ABC, abstractmethod
from http.cookiejar import MozillaCookieJar
import imghdr
import json
import logging
import logging.handlers
import os
from random import choice
import re
import sys
from urllib.request import build_opener, HTTPCookieProcessor, Request
from urllib.parse import urlencode, quote_plus

from bs4 import BeautifulSoup

USER_AGENT = choice([
    'Mozilla/5.0 (X11; Ubuntu; Linux i686 on x86_64; rv:60.0) Gecko/20100101 '
    'Firefox/60.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 '
    'Firefox/57.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:10.0) Gecko/20100101 '
    'Firefox/60.0'
])


class ConsoleFilter:
    '''
    A filter to avoid showing exceptions stack traces text in user is terminal.
    '''
    def filter(self, record):
        record.exc_info = None
        record.exc_text = None
        return True


class Downloader(ABC):
    """
    Abstract class base of all manga downloaders.
    """
    logfile = 'smd.log'
    verbose = False

    def __init__(self, name, lang, site_url):
        self.name = name
        self.lang = lang
        self.site_url = site_url
        cookie_jar = MozillaCookieJar()
        # cookie_jar.load('cookies.txt') # TODO: save and load cookies
        self.url_opener = build_opener(HTTPCookieProcessor(cookie_jar))
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
        chapter, or a list of URL where the images can be found using
        `get_image`.
        '''
        pass

    def get_image(self, image_url):
        '''
        When `get_images` doesn't return the images URLs this method must be
        overridden to get the image URL from the given URL.
        '''
        return image_url

    def download(self, manga, chapter_selectors=None):
        '''
        Searches for `manga` and, if found, downloads chapters given in
        `chapter_selectors` are downloaded.
        '''
        success = True
        try:
            self.logger.info("Searching for '%s' ...", manga)
            mangas = self.search(manga)
            if mangas:
                manga, url = Downloader.select_manga(mangas)
            else:
                return False
            manga_dir = self._mkdir(os.path.abspath('.'), manga)
            self.logger.info("Getting chapters list of '%s' ...", manga)
            chapters = self.get_chapters(url)
            self.logger.info("Found %i chapters for '%s'",
                             len(chapters), manga)
            chapters = self._select_chapters(chapters, chapter_selectors)
            self.logger.info("Selected %i chapters to download", len(chapters))
            self.logger.info("Downloading '%s':", manga)
            for chap_title, url in chapters:
                chap_dir = self._mkdir(manga_dir, chap_title)
                self.logger.info("Getting images list for chapter '%s' ...",
                                 chap_title)
                images = self.get_images(url)
                img_count = len(images)
                dcount = len(str(img_count))
                for i, url in enumerate(images, 1):
                    print("\r[{}] Downloading '{}' (image: {}/{})"
                          .format(self.name, chap_title, i, img_count), end='')
                    name = os.path.join(chap_dir, str(i).zfill(dcount))
                    self.download_img(self.get_image(url), name)
                if img_count > 0:
                    print()
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            # exec_type, exc_obj, exc_tb = sys.exc_info()
            self.logger.exception(ex)
            success = False
        return success

    def get_json(self, url, data=None, method='GET'):
        return json.loads(self.get(url, data=data, method=method, xhr=True))

    def download_img(self, url, name):
        img = self.get(url, decode=False)
        ext = imghdr.what("", h=img)
        ext = '' if ext is None else '.'+ext
        file_name = name+ext
        with open(file_name, 'bw') as outf:
            outf.write(img)
        return file_name

    def get(self, url, data=None, method='GET', xhr=False, decode=True):
        if data is None:
            data = {}
        method = method.upper()
        data = urlencode(data)
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
        errors = 0
        while True:
            try:
                self.logger.debug('Downloading: %s', url)
                with self.url_opener.open(Request(url, data, headers)) as resp:
                    if decode:
                        return resp.read().decode(errors='ignore')
                    else:
                        return resp.read()
            except ConnectionResetError as err:
                if errors > 5:
                    raise
                errors += 1
                self.logger.debug(err)

    def _init_logger(self):
        self.logger = logging.Logger(self.name)
        self.logger.parent = None
        fh = logging.handlers.RotatingFileHandler(Downloader.logfile,
                                                  maxBytes=10000000)
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        if Downloader.verbose:
            ch.setLevel(logging.DEBUG)
        else:
            ch.addFilter(ConsoleFilter())
            ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - '
                                      '%(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        formatter = logging.Formatter('[%(name)s] - '
                                      '%(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(fh)  # order is important because ConsoleFilter
        self.logger.addHandler(ch)

    def _select_chapters(self, chapters, selectors):
        '''
        chapters: a list of chapters.
        selectors: a string of comma=separated selectors.

        returns: a set of selected chapters.
        '''
        if not selectors:
            return chapters
        selectors = selectors.split(',')
        chaps = set()
        ignored_chaps = set()
        for selector in selectors:
            ignore = False
            selector = selector.replace(' ', '')
            s = selector[:]
            if s.startswith('!'):
                ignore = True
                s = s[1:]
            if set(s) - set('1234567890-:'):
                self.logger.error("Invalid chapter selector: '%s'", selector)
                sys.exit(1)
            try:
                s = s.split(':')
                if s[0]:
                    i = int(s[0])
                    if i > 0:
                        s[0] = str(i-1)
                s = ':'.join(s)
                ch = eval("chapters[{}]".format(s))
                if type(ch) is list:
                    if not ch:
                        self.logger.error("Selector '%s' did not selected "
                                          "any chapters.", selector)
                        sys.exit(1)
                    elif ignore:
                        ignored_chaps.update(ch)
                    else:
                        chaps.update(ch)
                else:
                    if ignore:
                        ignored_chaps.add(ch)
                    else:
                        chaps.add(ch)
            except (SyntaxError, ValueError):
                self.logger.error("Invalid chapter selector: '%s'", selector)
                sys.exit(1)
            except IndexError:
                self.logger.error("Chapter selector out of range: '%s'",
                                  selector)
                sys.exit(1)
        if not chaps:
            chaps = set(chapters)
        return chaps - ignored_chaps

    @staticmethod
    def select_manga(mangas):
        print("Found:")
        dcount = len(str(len(mangas)))
        for i, manga in enumerate(mangas, 1):
            print("{}. {}".format(str(i).rjust(dcount), manga[0]))
        while True:
            try:
                i = int(input("Select manga to download [1-{}]:"
                              .format(len(mangas)))) - 1
                if i >= 0 and i < len(mangas):
                    break
            except ValueError:
                pass
            print("Invalid selection. Try again.")
        return mangas[i]

    def _mkdir(self, dirname, basename):
        while True:
            path = os.path.join(dirname, basename)
            if os.path.exists(path):
                if not os.path.isdir(path):
                    self.logger.error("Can't create folder: File '%s' "
                                      "already exists.", basename)
                else:
                    break
            else:
                try:
                    os.mkdir(path)
                    break
                except FileNotFoundError:
                    self.logger.error("Can't create folder '%s': "
                                      "Invalid name.", basename)
            basename = input("Enter a new folder name:")
        return path

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
                            'http://{}.ninemanga.com'.format(site))

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
                results.extend((self.get_text(a), a['href']) for a in
                               direlist.find_all('a', class_='bookname'))
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
        url = '{}/buscar/{}.html'.format(self.site_url, quote_plus(manga))
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
        results = [(a['title'], a['href'])
                   for a in (div.find('div', 'media-body').a for div in divs)]
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
        results = [(sugg['value'], self.site_url+'/manga/'+sugg['data'])
                   for sugg in suggestions]
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
        return [(self.get_text(BeautifulSoup(result['name'], 'html.parser')),
                 self.site_url+'/manga/'+result['nameunsigned'])
                for result in data]

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
        data = self.get_json(url, {'query': manga})
        results = [(title, 'http:'+url)
                   for title, url in zip(data['suggestions'], data['data'])]
        return results

    def get_chapters(self, manga_url):
        soup = BeautifulSoup(self.get(manga_url), 'html.parser')
        ulist = soup.find('div', class_='detail_list').ul
        chapters = [(self.get_text(a), 'http:'+a['href'])
                    for a in ulist.find_all('a')]
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
