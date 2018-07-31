# -*- coding: utf-8 -*-
"""
.. module:: downloader

This module provides the downloaders able to grab content from the
supported sites.

.. moduleauthor:: Asiel Díaz Benítez <asieldbenitez@gmail.com>

"""

from abc import ABC, abstractmethod
from http.cookiejar import MozillaCookieJar
import imghdr
import json
import logging
import logging.handlers
import os
import re
from urllib.request import build_opener, HTTPCookieProcessor, Request, URLError
from urllib.parse import urlencode, quote_plus

from bs4 import BeautifulSoup

from smd.utils import (ConsoleFilter, Chapter, get_text, select_chapters,
                       select_manga, Manga, mkdir, USER_AGENT)


class Downloader(ABC):

    """Abstract class base of all manga downloaders."""

    logfile = 'smd.log'
    verbose = False

    def __init__(self, name, lang, site_url):
        """
        :param str name: the name of the downloader.
        :param str lang: the language of the downloader (ISO 639-1 code) or *
                         if the site have manga in multiple languages.
        :param str site_url: the URL of the web site of this downloader.
        """
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

    def __repr__(self):
        return '({}, {}, {})'.format(self.name, self.lang, self.site_url)

    @abstractmethod
    def search(self, manga):
        """Searches for mangas matching the given text.

        :param str manga: a frase or manga title to search.
        :return: a list of tuples each one with two strings: the title and
                 URL of a matched manga.
        """
        pass

    @abstractmethod
    def get_chapters(self, manga_url):
        """Extracts the manga chapters from the given manga URL.

        :param str manga_url: the URL of a manga.
        :return: a list of tuples each one with two strings: the title and
                 URL of a chapter from the given manga.
        """
        pass

    @abstractmethod
    def get_images(self, chapter_url):
        """Extracts the images links from a chapter URL.

        :param str chapter_url: the URL of a manga chapter.
        :return: list of image URLs for the given chapter, or a list of
                 URLs where the images can be extracted using
                 :func:`~smd.downloader.Downloader.get_image`.
        """
        pass

    @classmethod
    def get_image(cls, image_url):
        """If needed, extracts the image link from the given URL.

        :param str image_url: the image URL or an URL to a page where the image
                              link can be extracted.
        :return: the image URL.
        :rtype: str
        """
        return image_url

    def update(self, manga):
        """Downloads new available chapters of the given manga.

        :param manga: the manga to update.
        :type manga: :class:`~smd.utils.Manga`
        :return: the number of updated mangas.
        :rtype: int
        """
        self.logger.info(_("Looking for new chapters of '{}' ...")
                         .format(manga))
        all_chaps = self.get_chapters(manga['url'])
        old_chaps = [chap['title'] for chap in manga.chapters_iter()]
        new_chaps = [Chapter(mkdir(manga.path, title), title, url)
                     for title, url in all_chaps if title not in old_chaps]
        self.logger.info(_("Found {} new chapters for '{}'")
                         .format(len(new_chaps), manga))
        for chap in new_chaps:
            self._download_chapter(chap)
        updates = len(new_chaps)
        if updates == 0:
            self.logger.info(_("No new chapters found for '{}'.")
                             .format(manga))
        return updates

    def resume(self, manga):
        """Continues with the (unfinished) download of the given manga.

        :param manga: the manga to continue downloading.
        :type manga: :class:`~smd.utils.Manga`
        :return: the number of resumed mangas.
        :rtype: int
        """
        self.logger.info(_("Resuming download of '{}' ...").format(manga))
        downloads = 0
        for chap in manga.chapters_iter():
            if chap['current'] < len(chap['images']):
                self._download_chapter(chap)
                downloads += 1
        if downloads == 0:
            self.logger.warning(_("No pending chapters found for '{}'.")
                                .format(manga))
        return downloads

    def _download_chapter(self, chapter):
        """Downloads the given chapter only if it is not downloaded already,
        if the chapter was previously interrupted the download is resumed.

        :param chapter: the chapter to download.
        :type chapter: :class:`~smd.utils.Chapter`
        """
        if chapter['current'] == len(chapter['images']):
            self.logger.info(_("Skipping chapter '{}': Already downloaded.")
                             .format(chapter))
            return
        elif chapter['current'] == -1:
            self.logger.info(_("Getting images list for chapter '{}' ...")
                             .format(chapter))
            chapter['images'] = self.get_images(chapter['url'])
            chapter['current'] = 0
            chapter.save_data()
        img_count = len(chapter['images'])
        dcount = len(str(img_count))
        for url in chapter['images'][chapter['current']:]:
            current = chapter['current']+1
            print('\r'+_("[{}] Downloading '{}' (image: {}/{})").format(
                self.name, chapter, current, img_count), end='')
            name = os.path.join(chapter.path, str(current).zfill(dcount))
            self.download_img(self.get_image(url), name)
            chapter['current'] = current
            chapter.save_data()
        if img_count > 0:
            print()

    def download(self, manga, chapter_selectors=None):
        """Searches for the given manga and, if found, chapters specified in
        ``chapter_selectors`` are downloaded.

        :param str manga: the manga to download.
        :param str chapter_selectors: a string specifying the chapters to
                                      download.
        :return: ``True`` if the manga was downloaded successfully, ``False``
                 otherwise.
        """
        success = True
        try:
            self.logger.info(_("Searching for '{}' ...").format(manga))
            mangas = self.search(manga)
            if mangas:
                title, url = select_manga(mangas)
            else:
                return False
            manga = Manga(mkdir(os.path.abspath('.'), title),
                          title, url, self.name)
            manga.save_data()
            self.logger.info(_("Getting chapters list of '{}' ...")
                             .format(manga))
            chapters = self.get_chapters(url)
            self.logger.info(_("Found {} chapters for '{}'")
                             .format(len(chapters), manga))
            chapters = select_chapters(chapters, chapter_selectors)
            self.logger.info(_("Selected {} chapters to download")
                             .format(len(chapters)))
            self.logger.debug(_('Creating chapter folders...'))
            chapters = [Chapter(mkdir(manga.path, title), title, url)
                        for title, url in chapters]
            for chap in chapters:
                chap.save_data()
            self.logger.info(_("Downloading '{}':").format(manga))
            for chap in chapters:
                self._download_chapter(chap)
        except KeyboardInterrupt:
            raise
        except URLError as ex:
            self.logger.exception(ex)
            success = False
        return success

    def get_json(self, url, data=None, method='GET'):
        """Request json data from the given url.

        :param str url: the URL to request.
        :param dict data: the data to send in the request.
        :param str method: the method to use for the request.
        :return: the response data object.
        """
        return json.loads(self.get(url, data=data, method=method,
                                   xhr=True))

    def download_img(self, url, name):
        """Receives an image URL and a filename (without a file extension)
        and downloads the image, detects image format and save it to the
        given filename plus the proper extension.

        :param str url: the URL of the image.
        :param str name: the name to use for the saved image (without file
                         extension)
        :return: the file name with file extension  of the downloaded image.
        :rtype: str
        """
        img = self.get(url, decode=False)
        ext = imghdr.what("", h=img)
        ext = '' if ext is None else '.'+ext
        file_name = name+ext
        with open(file_name, 'bw') as outf:
            outf.write(img)
        return file_name

    def get(self, url, data=None, method='GET', xhr=False, decode=True):
        """Retrieves data from given URL.

        :param str url: the URL to retrieve.
        :param dict data: the data to send with the request.
        :param str method: the method to use to request the URL (POST/GET).
        :param bool xhr: if ``True`` set the header 'X-Requested-With' to
                         'XMLHttpRequest'
        :param bool decode: if ``True`` decode the response data.
        :return: the response data.
        :raises ConnectionResetError: if the connection is reset more than
                                      five times.
        """
        if data is None:
            data = {}
        method = method.upper()
        encoded_data = urlencode(data)
        del data
        if method == 'GET':
            if encoded_data:
                url = url+'?'+encoded_data
            encoded_data = None
        elif method == 'POST':
            encoded_data = encoded_data.encode('ascii')
        else:
            raise Exception(
                _("Only 'GET' and 'POST' methods are implemented."))
        if xhr:
            headers = {'X-Requested-With': 'XMLHttpRequest'}
        else:
            headers = {}
        errors = 0
        while True:
            try:
                self.logger.debug(_('Downloading: {}').format(url))
                req = Request(url, encoded_data, headers)
                with self.url_opener.open(req) as resp:
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
        """Initializes the downloader is logger."""
        self.logger = logging.Logger(self.name)
        self.logger.parent = None
        fhandler = logging.handlers.RotatingFileHandler(Downloader.logfile,
                                                        backupCount=1,
                                                        maxBytes=2000000)
        fhandler.setLevel(logging.DEBUG)
        chandler = logging.StreamHandler()
        if Downloader.verbose:
            chandler.setLevel(logging.DEBUG)
        else:
            chandler.addFilter(ConsoleFilter())
            chandler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - '
                                      '%(levelname)s - %(message)s')
        fhandler.setFormatter(formatter)
        formatter = logging.Formatter('[%(name)s] - '
                                      '%(levelname)s - %(message)s')
        chandler.setFormatter(formatter)
        # order is important because ConsoleFilter:
        self.logger.addHandler(fhandler)
        self.logger.addHandler(chandler)


class NineManga(Downloader):

    """Downloads manga from ninemanga.com."""

    def __init__(self, site):
        lang = 'pt' if site == 'br' else site
        Downloader.__init__(self, 'ninemanga-'+site, lang,
                            'http://{}.ninemanga.com'.format(site))

    def search(self, manga):
        url = self.site_url+"/search/"
        soup = BeautifulSoup(self.get(url, {'wd': manga}), 'html.parser')
        direlist = soup.find('ul', class_='direlist')
        results = [(get_text(a), a['href'])
                   for a in direlist.find_all('a', class_='bookname')]
        pagelist = soup.find('ul', class_='pagelist')
        if pagelist:
            # this get only first few pages:
            for page in pagelist.find_all('a')[1:-1]:
                soup = BeautifulSoup(self.get(page['href']), 'html.parser')
                direlist = soup.find('ul', class_='direlist')
                results.extend((get_text(a), a['href']) for a in
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

    """Downloads manga from heavenmanga.com."""

    def __init__(self):
        Downloader.__init__(self, 'heavenmanga', 'es',
                            'http://heavenmanga.com')

    def search(self, manga):
        # TODO: find a better way to do this:
        url = '{}/buscar/{}.html'.format(self.site_url, quote_plus(manga))
        # page restriction: len(manga) must to be >= 4
        soup = BeautifulSoup(self.get(url), 'html.parser')
        divs = soup.find_all('div', class_='cont_manga')
        return [(get_text(div.a.header), div.a['href'])
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

    """Downloads manga from www.mangareader.net."""

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
        chapters = [(get_text(a), self.site_url + a['href'])
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

    """Downloads manga from mangaall.net."""

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

    """Downloads manga from mangadoor.com."""

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
        chapters = [(get_text(a), a['href'])
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

    """Downloads manga from manganelo.com."""

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
        return [(get_text(BeautifulSoup(result['name'], 'html.parser')),
                 self.site_url+'/manga/'+result['nameunsigned'])
                for result in data]

    def get_chapters(self, manga_url):
        soup = BeautifulSoup(self.get(manga_url), 'html.parser')
        div = soup.find('div', class_='chapter-list')
        chapters = []
        for anchor in div.find_all('a'):
            if anchor['href'].startswith('/'):
                anchor['href'] = 'https:'+anchor['href']
            chapters.append((get_text(anchor), anchor['href']))
        chapters.reverse()
        return chapters

    def get_images(self, chapter_url):
        soup = BeautifulSoup(self.get(chapter_url), 'html.parser')
        div = soup.find('div', id='vungdoc')
        return [img['src'] for img in div.find_all('img')]


class MangaHere(Downloader):

    """Downloads manga from www.mangahere.cc."""

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
        chapters = [(get_text(a), 'http:'+a['href'])
                    for a in ulist.find_all('a')]
        chapters.reverse()
        return chapters

    def get_images(self, chapter_url):
        soup = BeautifulSoup(self.get(chapter_url), 'html.parser')
        opts = soup.find('select', class_='wid60').find_all('option')
        return ['http:'+opt['value']
                for opt in opts if get_text(opt) != 'Featured']

    def get_image(self, image_url):
        soup = BeautifulSoup(self.get(image_url), 'html.parser')
        return soup.find('img', id='image')['src']


def get_downloaders():
    """Creates a list with instances of all supported downloaders.

    :return: the list of all supported downloaders.
    :rtype: list of :class:`Downloader`
    """
    return [NineManga('en'), NineManga('es'), NineManga('ru'),
            NineManga('de'), NineManga('it'), NineManga('br'),
            HeavenManga(), MangaReader(), MangaAll(),
            MangaDoor(), MangaNelo(), MangaHere()]
