# -*- coding: utf-8 -*-
"""
.. module:: tests.test_downloader

Offline tests for the :mod:`smd.downloader` module.

"""
from io import BytesIO, StringIO
import json
import logging
import os
import shutil
import sys
import typing
import unittest
import urllib

import smd

if typing.TYPE_CHECKING:
    from typing import Callable, List

ROOT = os.path.dirname(os.path.abspath(__file__))  # type: str
DATA_DIR = os.path.join(ROOT, 'data', 'downloader')  # type: str
TEST_DIR = os.path.join(os.path.dirname(ROOT), 'test_downloader_temp')  # type:str


def setUpModule() -> None:
    os.mkdir(TEST_DIR)


def tearDownModule() -> None:
    shutil.rmtree(TEST_DIR)


def cached(fn: 'Callable') -> 'Callable':
    """Class to cache return values of dummy functions."""
    memo = {}  # type: dict
    def wrapper(*args, **kargs):
        try:
            return memo['result']
        except KeyError:
            memo['result'] = fn(*args, **kargs)
            return memo['result']
    return wrapper


class Downloader(smd.downloader.Downloader):

    """A Downloader class for testing abstract parent class
    :class:`smd.downloader.Downloader`
    """

    def __init__(self, name: str = 'downloader-test', lang: str = 'jp',
                 site_url: str = 'http://downloader-test.com') -> None:
        super().__init__(name, lang, site_url)

    def get_bytes(self, url: str, data: dict = None, method: str = 'GET',
                  xhr: bool = False) -> bytes:
        """Used to override :meth:`smd.downloader.Downloader.get_bytes`
        method to emulate online connection.
        """
        path = os.path.join(DATA_DIR, url)
        with open(path, 'rb') as file_handler:
            return file_handler.read()

    @cached
    def search(self, manga: str) -> 'List[smd.utils.Manga]':
        with open(os.path.join(DATA_DIR, 'search.json')) as data_fh:
            return  [smd.utils.Manga('', title, url, self.name)
                     for title, url in json.load(data_fh)]

    @cached
    def get_chapters(self, manga_url: str) -> 'List[smd.utils.Chapter]':
        with open(os.path.join(DATA_DIR, 'get_chapters.json')) as data_fh:
            return [smd.utils.Chapter('', title, url)
                    for title, url in json.load(data_fh)]

    @cached
    def get_images(self, chapter_url: str) -> 'List[str]':
        with open(os.path.join(DATA_DIR, 'get_images.json')) as data_fh:
            return json.load(data_fh)

    def get_image(self, image_url: str) -> str:
        try:
            return self._image[image_url]
        except AttributeError:
            with open(os.path.join(DATA_DIR, 'get_image.json')) as data_fh:
                self._image = json.load(data_fh)  # type: dict
            return self._image[image_url]


class TestDownloader(unittest.TestCase):

    """Tests :class:`smd.downloader.Downloader` class."""

    test_dir = None  # type: str
    data_dir = None  # type: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_dir = os.path.join(TEST_DIR, 'downloader')
        cls.data_dir = DATA_DIR
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)

    def setUp(self) -> None:
        self.downl = Downloader()

    def tearDown(self) -> None:
        sys.stdin.close()
        del self.downl

    def test_init(self) -> None:
        """Tests :meth:`smd.downloader.Downloader.__init__` method."""
        name = 'downloader-test'
        lang = 'jp'
        site_url = 'http://downloader-test.com'
        downl = Downloader(name, lang, site_url)
        self.assertEqual(downl.name, name)
        self.assertEqual(downl.lang, lang)
        self.assertEqual(downl.site_url, site_url)
        self.assertIsInstance(downl.url_opener, urllib.request.OpenerDirector)
        self.assertIsInstance(downl.logger, logging.Logger)
        del downl

    def test_str(self) -> None:
        """Tests :meth:`smd.downloader.Downloader.__str__` method."""
        self.assertEqual(str(self.downl), self.downl.name)

    def test_repr(self) -> None:
        """Tests :meth:`smd.downloader.Downloader.__repr__` method."""
        exp_repr = '({}, {}, {})'.format(self.downl.name, self.downl.lang,
                                         self.downl.site_url)
        self.assertEqual(repr(self.downl), exp_repr)

    def test_download_chapter(self) -> None:
        """Tests :meth:`smd.downloader.Downloader._download_chapter`
        function."""
        chap_dir = os.path.join(self.test_dir, 'test_download_chapter')
        shutil.copytree(os.path.join(self.data_dir, 'TestManga', 'chap1'),
                        chap_dir)
        chap = smd.utils.Chapter(chap_dir, 'title', 'url')
        self.downl._download_chapter(chap)
        self.assertEqual(chap.current, 3)
        self.assertEqual(chap.current, len(chap.images))
        self.downl._download_chapter(chap)
        self.assertEqual(chap.current, 3)
        chap.current, chap.images = 1, [self.downl.get_images('')[0]]*5
        self.downl._download_chapter(chap)
        self.assertEqual(chap.current, 5)

    def test_init_logger(self) -> None:
        """Tests :meth:`smd.downloader.Downloader._init_logger` method."""
        self.downl.logger.handlers[0].close()
        del self.downl.logger
        self.downl._init_logger()
        self.assertIsInstance(self.downl.logger, logging.Logger)

    def test_download(self) -> None:
        """Tests :meth:`smd.downloader.Downloader.download` method."""
        manga_dir = 'PROBLEMATIC NARUTO'
        sys.stdin = StringIO('3\n'+manga_dir)
        self.assertTrue(self.downl.download('naruto', '1:3'))
        self.assertEqual(sys.stdin.read(), '')
        manga_dir = os.path.join(self.test_dir, manga_dir)
        self.assertTrue(manga_dir)
        self.assertTrue(os.path.isfile(
            os.path.join(manga_dir, smd.utils.Manga.data_filename)))
        for i in range(1, 4):
            path = os.path.join(manga_dir, str(i).zfill(6),
                                smd.utils.Chapter.data_filename)
            with self.subTest(i=i):
                self.assertTrue(os.path.isfile(path))

    def test_download_img(self) -> None:
        """Tests :meth:`smd.downloader.Downloader.download_img` method."""
        self.downl.download_img('images/img1.jpeg', 'test_01')
        with open('test_01.jpeg', 'rb') as img_fh:
            img = img_fh.read()
        exp_img = self.downl.get_bytes('images/img1.jpeg')
        self.assertEqual(img, exp_img)

    def test_get_bytes(self) -> None:
        """Tests :meth:`smd.downloader.Downloader.get_bytes` method."""
        exp_resp = b'tests passed'

        def url_open1(req):
            return BytesIO(exp_resp)

        def url_open2(req):
            raise ConnectionResetError

        self.downl.url_opener.open = url_open1  # type: ignore
        url = 'http://test.com'
        resp = smd.downloader.Downloader.get_bytes(self.downl, url)
        self.assertEqual(resp, exp_resp)
        data = {'user': 'name', 'password': 'passwd'}
        resp = smd.downloader.Downloader.get_bytes(self.downl, url, data)
        self.assertEqual(resp, exp_resp)
        resp = smd.downloader.Downloader.get_bytes(self.downl, url, data,
                                                   'POST', True)
        self.assertEqual(resp, exp_resp)
        with self.assertRaises(ValueError):
            smd.downloader.Downloader.get_bytes(self.downl, url, method='UNKNOW')
        self.downl.url_opener.open = url_open2  # type: ignore
        with self.assertRaises(ConnectionResetError):
            smd.downloader.Downloader.get_bytes(self.downl, url)

    def test_get_image(self) -> None:
        """Tests :meth:`smd.downloader.Downloader.get_image` method."""
        exp_img = 'test-image'
        img = smd.downloader.Downloader.get_image(self.downl, exp_img)
        self.assertEqual(img, exp_img)

    def test_get_json(self) -> None:
        """Tests :meth:`smd.downloader.Downloader.get_json` method."""
        data = self.downl.get_json('test.json')
        exp_data = json.loads(self.downl.get_str('test.json'))
        self.assertEqual(data, exp_data)

    def test_get_str(self) -> None:
        """Tests :meth:`smd.downloader.Downloader.get_str` method."""
        self.downl.get_bytes = lambda url: b'Testing get_str()'  # type: ignore
        self.assertEqual(self.downl.get_str('url'), 'Testing get_str()')

    def test_resume(self) -> None:
        """Tests :meth:`smd.downloader.Downloader.resume` method."""
        def download_chapter(chap: smd.utils.Chapter):
            resumed_chaps.append([chap.title, chap.url])
        resumed_chaps = []  # type: List[List[str]]
        manga_dir = os.path.join(self.test_dir, 'test_resume')
        shutil.copytree(os.path.join(self.data_dir, 'TestManga'), manga_dir)
        manga = smd.utils.Manga.from_folder(manga_dir)
        self.downl._download_chapter = download_chapter  # type: ignore
        self.downl.resume(manga)
        data_file = os.path.join(self.data_dir, 'resumed_chaps.json')
        with open(data_file) as data_fh:
            exp_resumed_chaps = json.load(data_fh)
        self.assertEqual(resumed_chaps, exp_resumed_chaps)

    def test_update(self) -> None:
        """Tests :meth:`smd.downloader.Downloader.update` method."""
        def download_chapter(chap: smd.utils.Chapter):
            new_chaps.append([chap.title, chap.url])
        new_chaps = []  # type: List[List[str]]
        manga_dir = os.path.join(self.test_dir, 'test_update')
        shutil.copytree(os.path.join(self.data_dir, 'TestManga'), manga_dir)
        manga = smd.utils.Manga.from_folder(manga_dir)
        self.downl._download_chapter = download_chapter  # type: ignore
        self.downl.update(manga)
        with open(os.path.join(self.data_dir, 'new_chaps.json')) as data_fh:
            exp_new_chaps = json.load(data_fh)
        self.assertEqual(new_chaps, exp_new_chaps)


class TestNineManga(unittest.TestCase):

    """Tests :class:`smd.downloader.NineManga` class."""

    test_dir = None  # type: str
    data_dir = None  # type: str
    downl = None     # type: smd.downloader.NineManga

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_dir = os.path.join(TEST_DIR, 'ninemanga')
        cls.data_dir = os.path.join(DATA_DIR, 'ninemanga')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = smd.downloader.NineManga('en')
        cls.downl.get_str = cls.get_str  # type: ignore

    @classmethod
    def tearDownClass(cls) -> None:
        del cls.downl

    @classmethod
    def get_str(cls, url: str, data: dict = None) -> str:
        """Used to override :meth:`smd.downloader.Downloader.get_str`
        method to emulate online connection.
        """
        if url.endswith('/search/'):
            data_name = 'search/'+data['wd']+'.html'  # type: ignore
        else:
            data_name = url
        path = os.path.join(cls.data_dir, data_name)
        with open(path) as file_handler:
            return file_handler.read()

    def test_init(self) -> None:
        """Tests :meth:`smd.downloader.NineManga.__init__` method."""
        self.assertEqual(self.downl.name, 'ninemanga-en')
        self.assertEqual(self.downl.lang, 'en')
        self.assertEqual(self.downl.site_url, 'http://en.ninemanga.com')

    def test_search(self) -> None:
        """Tests :meth:`smd.downloader.NineManga.search` method."""
        results = [(d.title, d.url) for d in self.downl.search('naruto')]
        with open(os.path.join(self.data_dir, 'search.json')) as data_fh:
            exp_res = [(title, url) for title, url in json.load(data_fh)]
        self.assertEqual(results, exp_res)

    def test_get_chapters(self) -> None:
        """Tests :meth:`smd.downloader.NineManga.get_chapters` method."""
        chaps = self.downl.get_chapters('mangas/naruto1_warning.html')
        chapters = [(c.title, c.url) for c in chaps]
        with open(os.path.join(self.data_dir, 'get_chapters.json')) as data_fh:
            exp_chaps = [(title, url) for title, url in json.load(data_fh)]
        self.assertEqual(chapters, exp_chaps)

    def test_get_images(self) -> None:
        """Tests :meth:`smd.downloader.NineManga.get_images` method."""
        site_url = self.downl.site_url
        images_pages = self.downl.get_images(
            'image_pages/naruto1_ch1_img1.html')
        with open(os.path.join(self.data_dir, 'get_images.json')) as data_fh:
            exp_pages = [site_url+link for link in json.load(data_fh)]
        self.assertEqual(images_pages, exp_pages)

    def test_get_image(self) -> None:
        """Tests :meth:`smd.downloader.NineManga.get_image` method."""
        with open(os.path.join(self.data_dir, 'get_image.json')) as data_fh:
            exp_imgs = json.load(data_fh)
        for url, exp_img in exp_imgs.items():
            with self.subTest(exp_img=exp_img):
                image = self.downl.get_image(url)
                self.assertEqual(image, exp_img)


class TestHeavenManga(unittest.TestCase):

    """Tests :class:`smd.downloader.HeavenManga` class."""

    test_dir = None  # type: str
    data_dir = None  # type: str
    downl = None     # type: smd.downloader.HeavenManga

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_dir = os.path.join(TEST_DIR, 'heavenmanga')
        cls.data_dir = os.path.join(DATA_DIR, 'heavenmanga')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = smd.downloader.HeavenManga()
        cls.downl.get_str = cls.get_str  # type: ignore

    @classmethod
    def tearDownClass(cls) -> None:
        del cls.downl

    @classmethod
    def get_str(cls, url: str) -> str:
        """Method used to override the :meth:`smd.downloader.Downloader.get_str`
        method to emulate online connection.
        """
        search_url = TestHeavenManga.downl.site_url+'/buscar/'
        if url.startswith(search_url):
            data_name = os.path.join('search', url.replace(search_url, ''))
        else:
            data_name = url
        path = os.path.join(TestHeavenManga.data_dir, data_name)
        with open(path) as file_handler:
            return file_handler.read()

    def test_init(self) -> None:
        """Tests :meth:`smd.downloader.HeavenManga.__init__` method."""
        self.assertEqual(self.downl.name, 'heavenmanga')
        self.assertEqual(self.downl.lang, 'es')
        self.assertEqual(self.downl.site_url, 'http://heavenmanga.com')

    def test_search(self) -> None:
        """Tests :meth:`smd.downloader.HeavenManga.search` method."""
        results = [(d.title, d.url) for d in self.downl.search('naruto')]
        with open(os.path.join(self.data_dir, 'search.json')) as data_fh:
            exp_res = [(title, url) for title, url in json.load(data_fh)]
        self.assertEqual(results, exp_res)

    def test_get_chapters(self) -> None:
        """Tests :meth:`smd.downloader.HeavenManga.get_chapters` method."""
        chapters = [(c.title, c.url)
                    for c in self.downl.get_chapters('mangas/naruto1.html')]
        with open(os.path.join(self.data_dir, 'get_chapters.json')) as data_fh:
            exp_chaps = [(title, url) for title, url in json.load(data_fh)]
        self.assertEqual(chapters, exp_chaps)

    def test_get_images(self) -> None:
        """Tests :meth:`smd.downloader.HeavenManga.get_images` method."""
        images_pages = self.downl.get_images('chapter_pages/naruto1_ch1.html')
        with open(os.path.join(self.data_dir, 'get_images.json')) as data_fh:
            exp_pages = json.load(data_fh)  # type: List[str]
        self.assertEqual(images_pages, exp_pages)

    def test_get_image(self) -> None:
        """Tests :meth:`smd.downloader.HeavenManga.get_image` method."""
        with open(os.path.join(self.data_dir, 'get_image.json')) as data_fh:
            exp_imgs = json.load(data_fh)
        for url, exp_img in exp_imgs.items():
            with self.subTest(exp_img=exp_img):
                image = self.downl.get_image(url)
                self.assertEqual(image, exp_img)


class TestMangaReader(unittest.TestCase):

    """Tests :class:`smd.downloader.MangaReader` class."""

    test_dir = None  # type: str
    data_dir = None  # type: str
    downl = None     # type: smd.downloader.MangaReader

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_dir = os.path.join(TEST_DIR, 'mangareader')
        cls.data_dir = os.path.join(DATA_DIR, 'mangareader')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = smd.downloader.MangaReader()
        cls.downl.get_str = cls.get_str  # type: ignore

    @classmethod
    def tearDownClass(cls) -> None:
        del cls.downl

    @classmethod
    def get_str(cls, url: str, data: dict = None) -> str:
        """Used to override the :meth:`smd.downloader.Downloader.get_str`
        method to emulate online connection.
        """
        if url.endswith('/actions/search/'):
            data_name = 'search/'+data['q']+'.html'  # type: ignore
        else:
            data_name = url
        path = os.path.join(TestMangaReader.data_dir, data_name)
        with open(path) as file_handler:
            return file_handler.read()

    def test_init(self) -> None:
        """Tests :meth:`smd.downloader.MangaReader.__init__` method."""
        self.assertEqual(self.downl.name, 'mangareader')
        self.assertEqual(self.downl.lang, 'en')
        self.assertEqual(self.downl.site_url, 'https://www.mangareader.net')

    def test_search(self) -> None:
        """Tests :meth:`smd.downloader.MangaReader.search` method."""
        site_url = self.downl.site_url
        results = [(d.title, d.url) for d in self.downl.search('naruto')]
        with open(os.path.join(self.data_dir, 'search.json')) as data_fh:
            exp_res = [(l[0], site_url+'/'+l[1]) for l in json.load(data_fh)]
        self.assertEqual(results, exp_res)

    def test_get_chapters(self) -> None:
        """Tests :meth:`smd.downloader.MangaReader.get_chapters` method."""
        site_url = self.downl.site_url
        chapters = [(c.title, c.url)
                    for c in self.downl.get_chapters('mangas/naruto1.html')]
        with open(os.path.join(self.data_dir, 'get_chapters.json')) as data_fh:
            exp_chaps = [(l[0], site_url+'/'+l[1]) for l in json.load(data_fh)]
        self.assertEqual(chapters, exp_chaps)

    def test_get_images(self) -> None:
        """Tests :meth:`smd.downloader.MangaReader.get_images` method."""
        site_url = self.downl.site_url
        images_pages = self.downl.get_images(
            'image_pages/naruto1_ch1_img1.html')
        with open(os.path.join(self.data_dir, 'get_images.json')) as data_fh:
            exp_pages = [site_url+'/'+l for l in json.load(data_fh)]
        self.assertEqual(images_pages, exp_pages)

    def test_get_image(self) -> None:
        """Tests :meth:`smd.downloader.MangaReader.get_image` method."""
        with open(os.path.join(self.data_dir, 'get_image.json')) as data_fh:
            exp_imgs = json.load(data_fh)
        for url, exp_img in exp_imgs.items():
            with self.subTest(exp_img=exp_img):
                image = self.downl.get_image(url)
                self.assertEqual(image, exp_img)


class TestMangaAll(unittest.TestCase):

    """Tests :class:`smd.downloader.MangaAll` class."""

    test_dir = None  # type: str
    data_dir = None  # type: str
    downl = None     # type: smd.downloader.MangaAll

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_dir = os.path.join(TEST_DIR, 'mangaall')
        cls.data_dir = os.path.join(DATA_DIR, 'mangaall')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = smd.downloader.MangaAll()
        cls.downl.get_str = cls.get_str  # type: ignore

    @classmethod
    def tearDownClass(cls) -> None:
        del cls.downl

    @classmethod
    def get_str(cls, url: str, data: dict = None) -> str:
        """Used to override the :meth:`smd.downloader.Downloader.get`
        method to emulate online connection.
        """
        if url.endswith('/search/'):
            data_name = 'search/'+data['q']+'.html'  # type: ignore
        else:
            data_name = url
        path = os.path.join(TestMangaAll.data_dir, data_name)
        with open(path) as file_handler:
            return file_handler.read()

    def test_init(self) -> None:
        """Tests :meth:`smd.downloader.MangaAll.__init__` method."""
        self.assertEqual(self.downl.name, 'mangaall')
        self.assertEqual(self.downl.lang, 'en')
        self.assertEqual(self.downl.site_url, 'http://mangaall.net')

    def test_search(self) -> None:
        """Tests :meth:`smd.downloader.MangaAll.search` method."""
        results = [(d.title, d.url) for d in self.downl.search('naruto')]
        with open(os.path.join(self.data_dir, 'search.json')) as data_fh:
            exp_res = [(title, url) for title, url in json.load(data_fh)]
        self.assertEqual(results, exp_res)

    def test_get_chapters(self) -> None:
        """Tests :meth:`smd.downloader.MangaAll.get_chapters` method."""
        chapters = [(c.title, c.url)
                    for c in self.downl.get_chapters('mangas/naruto1.html')]
        with open(os.path.join(self.data_dir, 'get_chapters.json')) as data_fh:
            exp_chaps = [(title, url) for title, url in json.load(data_fh)]
        self.assertEqual(chapters, exp_chaps)

    def test_get_images(self) -> None:
        """Tests :meth:`smd.downloader.MangaAll.get_images` method."""
        images_pages = self.downl.get_images(
            'image_pages/naruto1_ch1_img1.html')
        with open(os.path.join(self.data_dir, 'get_images.json')) as data_fh:
            exp_pages = json.load(data_fh)
        self.assertEqual(images_pages, exp_pages)

    def test_get_image(self) -> None:
        """Tests :meth:`smd.downloader.MangaAll.get_image` method."""
        with open(os.path.join(self.data_dir, 'get_image.json')) as data_fh:
            exp_imgs = json.load(data_fh)
        for url, exp_img in exp_imgs.items():
            with self.subTest(exp_img=exp_img):
                image = self.downl.get_image(url)
                self.assertEqual(image, exp_img)


class TestMangaDoor(unittest.TestCase):

    """Tests :class:`smd.downloader.MangaDoor` class."""

    test_dir = None  # type: str
    data_dir = None  # type: str
    downl = None     # type: smd.downloader.MangaDoor

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_dir = os.path.join(TEST_DIR, 'mangadoor')
        cls.data_dir = os.path.join(DATA_DIR, 'mangadoor')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = smd.downloader.MangaDoor()
        cls.downl.get_str = cls.get_str  # type: ignore

    @classmethod
    def tearDownClass(cls) -> None:
        del cls.downl

    @classmethod
    def get_str(cls, url: str, data: dict = None, method: str = 'GET',
                xhr: bool = False) -> str:
        """Used to override the :meth:`smd.downloader.Downloader.get_str`
        method to emulate online connection.
        """
        if url.endswith('/search/'):
            data_name = 'search/'+data['query']+'.json'  # type: ignore
        else:
            data_name = url
        path = os.path.join(TestMangaDoor.data_dir, data_name)
        with open(path) as file_handler:
            return file_handler.read()

    def test_init(self) -> None:
        """Tests :meth:`smd.downloader.MangaDoor.__init__` method."""
        self.assertEqual(self.downl.name, 'mangadoor')
        self.assertEqual(self.downl.lang, 'es')
        self.assertEqual(self.downl.site_url, 'http://mangadoor.com')

    def test_search(self) -> None:
        """Tests :meth:`smd.downloader.MangaDoor.search` method."""
        site_url = self.downl.site_url
        results = [(d.title, d.url) for d in self.downl.search('naruto')]
        with open(os.path.join(self.data_dir, 'search.json')) as data_fh:
            exp_res = [(l[0], site_url+'/'+l[1]) for l in json.load(data_fh)]
        self.assertEqual(results, exp_res)

    def test_get_chapters(self) -> None:
        """Tests :meth:`smd.downloader.MangaDoor.get_chapters` method."""
        chapters = [(c.title, c.url)
                    for c in self.downl.get_chapters('mangas/naruto1.html')]
        with open(os.path.join(self.data_dir, 'get_chapters.json')) as data_fh:
            exp_chaps = [(title, url) for title, url in json.load(data_fh)]
        self.assertEqual(chapters, exp_chaps)

    def test_get_images(self) -> None:
        """Tests :meth:`smd.downloader.MangaDoor.get_images` method."""
        chap_url = 'image_pages/naruto1_ch1_img1.html'
        images_pages = self.downl.get_images(chap_url)
        with open(os.path.join(self.data_dir, 'get_images.json')) as data_fh:
            exp_pages = [chap_url+'/'+l for l in json.load(data_fh)]
        self.assertEqual(images_pages, exp_pages)

    def test_get_image(self) -> None:
        """Tests :meth:`smd.downloader.MangaDoor.get_image` method."""
        with open(os.path.join(self.data_dir, 'get_image.json')) as data_fh:
            exp_imgs = json.load(data_fh)
        for url, exp_img in exp_imgs.items():
            with self.subTest(exp_img=exp_img):
                image = self.downl.get_image(url)
                self.assertEqual(image, exp_img)


class TestMangaNelo(unittest.TestCase):

    """Tests :class:`smd.downloader.MangaNelo` class."""

    test_dir = None  # type: str
    data_dir = None  # type: str
    downl = None     # type: smd.downloader.MangaNelo

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_dir = os.path.join(TEST_DIR, 'manganelo')
        cls.data_dir = os.path.join(DATA_DIR, 'manganelo')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = smd.downloader.MangaNelo()
        cls.downl.get_str = cls.get_str  # type: ignore

    @classmethod
    def tearDownClass(cls) -> None:
        del cls.downl

    @classmethod
    def get_str(cls, url: str, data: dict = None, method: str = 'GET',
                xhr: bool = False) -> str:
        """Used to override the :meth:`smd.downloader.Downloader.get_str`
        method to emulate online connection.
        """
        if url.endswith('/home_json_search/'):
            data_name = 'search/'+data['searchword']+'.json'  # type: ignore
        else:
            data_name = url
        path = os.path.join(TestMangaNelo.data_dir, data_name)
        with open(path) as file_handler:
            return file_handler.read()

    def test_init(self) -> None:
        """Tests :meth:`smd.downloader.MangaNelo.__init__` method."""
        self.assertEqual(self.downl.name, 'manganelo')
        self.assertEqual(self.downl.lang, 'en')
        self.assertEqual(self.downl.site_url, 'https://manganelo.com')

    def test_search(self) -> None:
        """Tests :meth:`smd.downloader.MangaNelo.search` method."""
        site_url = self.downl.site_url
        results = [(d.title, d.url) for d in self.downl.search('naruto')]
        with open(os.path.join(self.data_dir, 'search.json')) as data_fh:
            exp_res = [(l[0], site_url+'/'+l[1]) for l in json.load(data_fh)]
        self.assertEqual(results, exp_res)

    def test_get_chapters(self) -> None:
        """Tests :meth:`smd.downloader.MangaNelo.get_chapters` method."""
        chapters = [(c.title, c.url)
                    for c in self.downl.get_chapters('mangas/naruto1.html')]
        with open(os.path.join(self.data_dir, 'get_chapters.json')) as data_fh:
            exp_chaps = [(title, url) for title, url in json.load(data_fh)]
        self.assertEqual(chapters, exp_chaps)

    def test_get_images(self) -> None:
        """Tests :meth:`smd.downloader.MangaNelo.get_images` method."""
        chap_url = 'image_pages/naruto1_ch1.html'
        images_pages = self.downl.get_images(chap_url)
        with open(os.path.join(self.data_dir, 'get_images.json')) as data_fh:
            exp_pages = json.load(data_fh)
        self.assertEqual(images_pages, exp_pages)


class TestMangaHere(unittest.TestCase):

    """Tests :class:`smd.downloader.MangaHere` class."""

    test_dir = None  # type: str
    data_dir = None  # type: str
    downl = None     # type: smd.downloader.MangaHere

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_dir = os.path.join(TEST_DIR, 'mangahere')
        cls.data_dir = os.path.join(DATA_DIR, 'mangahere')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = smd.downloader.MangaHere()
        cls.downl.get_str = cls.get_str  # type: ignore

    @classmethod
    def tearDownClass(cls) -> None:
        del cls.downl

    @classmethod
    def get_str(cls, url: str, data: dict = None, method: str = 'GET',
                xhr: bool = False) -> str:
        """Used to override the :meth:`smd.downloader.Downloader.get_str`
        method to emulate online connection.
        """
        if url.endswith('/ajax/search.php'):
            data_name = 'search/'+data['query']+'.json'  # type: ignore
        else:
            data_name = url
        path = os.path.join(TestMangaHere.data_dir, data_name)
        with open(path) as file_handler:
            return file_handler.read()

    def test_init(self) -> None:
        """Tests :meth:`smd.downloader.MangaHere.__init__` method."""
        self.assertEqual(self.downl.name, 'mangahere')
        self.assertEqual(self.downl.lang, 'en')
        self.assertEqual(self.downl.site_url, 'http://www.mangahere.cc')

    def test_search(self) -> None:
        """Tests :meth:`smd.downloader.MangaHere.search` method."""
        results = [(d.title, d.url) for d in self.downl.search('naruto')]
        with open(os.path.join(self.data_dir, 'search.json')) as data_fh:
            exp_res = [(title, url) for title, url in json.load(data_fh)]
        self.assertEqual(results, exp_res)

    def test_get_chapters(self) -> None:
        """Tests :meth:`smd.downloader.MangaHere.get_chapters` method."""
        chapters = [(c.title, c.url)
                    for c in self.downl.get_chapters('mangas/naruto1.html')]
        with open(os.path.join(self.data_dir, 'get_chapters.json')) as data_fh:
            exp_chaps = [(title, url) for title, url in json.load(data_fh)]
        self.assertEqual(chapters, exp_chaps)

    def test_get_images(self) -> None:
        """Tests :meth:`smd.downloader.MangaHere.get_images` method."""
        chap_url = 'image_pages/naruto1_ch1_img1.html'
        images_pages = self.downl.get_images(chap_url)
        with open(os.path.join(self.data_dir, 'get_images.json')) as data_fh:
            exp_pages = json.load(data_fh)
        self.assertEqual(images_pages, exp_pages)

    def test_get_image(self) -> None:
        """Tests :meth:`smd.downloader.MangaHere.get_image` method."""
        with open(os.path.join(self.data_dir, 'get_image.json')) as data_fh:
            exp_imgs = json.load(data_fh)
        for url, exp_img in exp_imgs.items():
            with self.subTest(exp_img=exp_img):
                image = self.downl.get_image(url)
                self.assertEqual(image, exp_img)


class TestFuntions(unittest.TestCase):

    """Tests functions on :mod:`smd.downloader` module."""

    def test_get_downloaders(self) -> None:
        """Tests :func:`smd.downloader.get_downloaders` function."""
        downloaders = smd.downloader.get_downloaders()
        self.assertEqual(len(downloaders), 12)
        for d in downloaders:
            with self.subTest(d=d):
                self.assertIsInstance(d, smd.downloader.Downloader)
