# -*- coding: utf-8 -*-
"""
.. module:: tests.test_downloader

Offline tests for the :mod:`smd.downloader` module.

"""

from io import StringIO
import json
import os
import shutil
import sys
import unittest

import smd.downloader as downloader
import smd.utils as utils

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, 'data', 'downloader')
TEST_DIR = os.path.join(os.path.dirname(ROOT), 'test_downloader_temp')


def setUpModule():
    """Creates a temporal directory where the tests are run."""
    os.mkdir(TEST_DIR)


def tearDownModule():
    """Removes the temporal tests directory."""
    shutil.rmtree(TEST_DIR)


class Downloader(downloader.Downloader):

    """A Downloader class for testing abstract parent class
    :class:`smd.downloader.Downloader`"""

    def __init__(self, name='downloader-test', lang='jp',
                 site_url='http://downloader-test.com'):
        downloader.Downloader.__init__(self, name, lang, site_url)

    def get(self, url, data=None, method='GET', xhr=False, decode=True):
        path = os.path.join(DATA_DIR, url)
        with open(path, 'rb') as file_handler:
            if decode:
                return file_handler.read().decode(errors='ignore')
            else:
                return file_handler.read()

    def search(self, manga):
        with open(os.path.join(DATA_DIR, 'search.json')) as data_fh:
            return [tuple(l) for l in json.load(data_fh)]

    def get_chapters(self, manga_url):
        with open(os.path.join(DATA_DIR, 'get_chapters.json')) as data_fh:
            return [tuple(l) for l in json.load(data_fh)]

    def get_images(self, chapter_url):
        with open(os.path.join(DATA_DIR, 'get_images.json')) as data_fh:
            return json.load(data_fh)

    def get_image(self, image_url):
        with open(os.path.join(DATA_DIR, 'get_image.json')) as data_fh:
            return json.load(data_fh)[image_url]


class TestDownloader(unittest.TestCase):

    """Tests :class:`smd.downloader.Downloader` class."""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.join(TEST_DIR, 'downloader')
        cls.data_dir = DATA_DIR
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = Downloader()

    @classmethod
    def tearDownClass(cls):
        cls.downl.logger.handlers[0].close()

    def tearDown(self):
        sys.stdin.close()

    def test_init(self):
        """Tests :meth:`smd.downloader.Downloader.__init__` function."""
        site_url = 'http://downloader-test.com'
        self.assertEqual(self.downl.name, 'downloader-test')
        self.assertEqual(self.downl.lang, 'jp')
        self.assertEqual(self.downl.site_url, site_url)

    def test_str(self):
        """Tests :meth:`smd.downloader.Downloader.__str__` function."""
        name = 'downloader-test'
        self.assertEqual(str(self.downl), name)

    def test_repr(self):
        """Tests :meth:`smd.downloader.Downloader.__repr__` function."""
        name = 'downloader-test'
        lang = 'jp'
        site_url = 'http://downloader-test.com'
        exp_repr = '({}, {}, {})'.format(name, lang, site_url)
        self.assertEqual(repr(self.downl), exp_repr)

    def test_update(self):
        """Tests :meth:`smd.downloader.Downloader.update` function."""
        new_chaps = []
        manga_dir = os.path.join(self.test_dir, 'TestManga_update')
        shutil.copytree(os.path.join(self.data_dir, 'TestManga'), manga_dir)
        manga = utils.Manga.from_folder(manga_dir)
        download_chapter = self.downl._download_chapter
        self.downl._download_chapter = lambda chap: new_chaps.append(
            [chap['title'], chap['url']])
        self.downl.update(manga)
        self.downl._download_chapter = download_chapter
        with open(os.path.join(self.data_dir, 'new_chaps.json')) as data_fh:
            exp_new_chaps = json.load(data_fh)
        self.assertEqual(new_chaps, exp_new_chaps)

    def test_resume(self):
        """Tests :meth:`smd.downloader.Downloader.resume` function."""
        resumed_chaps = []
        manga_dir = os.path.join(self.test_dir, 'TestManga_resume')
        shutil.copytree(os.path.join(self.data_dir, 'TestManga'), manga_dir)
        manga = utils.Manga.from_folder(manga_dir)
        download_chapter = self.downl._download_chapter
        self.downl._download_chapter = lambda chap: resumed_chaps.append(
            [chap['title'], chap['url']])
        self.downl.resume(manga)
        self.downl._download_chapter = download_chapter
        data_file = os.path.join(self.data_dir, 'resumed_chaps.json')
        with open(data_file) as data_fh:
            exp_resumed_chaps = json.load(data_fh)
        self.assertEqual(resumed_chaps, exp_resumed_chaps)

    def test_download_chapter(self):
        """Tests :meth:`smd.downloader.Downloader._download_chapter`
        function."""
        chap = utils.Chapter('', 'test-chap')
        self.downl._download_chapter(chap)
        self.assertEqual(chap['current'], 3)
        self.assertEqual(chap['current'], len(chap['images']))
        self.downl._download_chapter(chap)
        self.assertEqual(chap['current'], 3)
        chap = utils.Chapter('', 'test-chap')
        chap['current'], chap['images'] = 1, [self.downl.get_images('')[0]]*5
        self.downl._download_chapter(chap)
        self.assertEqual(chap['current'], 5)

    def test_download(self):
        """Tests :meth:`smd.downloader.Downloader.download` function."""
        manga_dir = 'PROBLEMATIC NARUTO'
        sys.stdin = StringIO('3\n'+manga_dir)
        self.assertTrue(self.downl.download('naruto', '1:3'))
        manga_dir = os.path.join(self.test_dir, manga_dir)
        self.assertTrue(manga_dir)
        self.assertTrue(os.path.isfile(
            os.path.join(manga_dir, utils.Manga._filename)))
        for title, __ in self.downl.get_chapters('')[0:3]:
            path = os.path.join(manga_dir, title, utils.Chapter._filename)
            with self.subTest(title=title):
                self.assertTrue(os.path.isfile(path))

    def test_get_json(self):
        """Tests :meth:`smd.downloader.Downloader.get_json` function."""
        data = self.downl.get_json('test.json')
        exp_data = json.loads(self.downl.get('test.json'))
        self.assertEqual(data, exp_data)

    def test_download_img(self):
        """Tests :meth:`smd.downloader.Downloader.download_img` function."""
        self.downl.download_img('images/img1.jpeg', 'test_01')
        with open('test_01.jpeg', 'rb') as img_fh:
            img = img_fh.read()
        exp_img = self.downl.get('images/img1.jpeg', decode=False)
        self.assertEqual(img, exp_img)


class TestNineManga(unittest.TestCase):

    """Tests :class:`smd.downloader.NineManga` class."""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.join(TEST_DIR, 'ninemanga')
        cls.data_dir = os.path.join(DATA_DIR, 'ninemanga')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = downloader.NineManga('en')
        cls.downl.get = cls.get

    @classmethod
    def tearDownClass(cls):
        cls.downl.logger.handlers[0].close()

    @classmethod
    def get(cls, url, data=None):
        """Method used to override :meth:`smd.downloader.Downloader.get`
        method to emulate online connection."""
        if url.endswith('/search/'):
            data_name = 'search/'+data['wd']+'.html'
        else:
            data_name = url
        path = os.path.join(TestNineManga.data_dir, data_name)
        with open(path) as file_handler:
            return file_handler.read()

    def test_init(self):
        """Tests :meth:`smd.downloader.NineManga.__init__` function."""
        self.assertEqual(self.downl.name, 'ninemanga-en')
        self.assertEqual(self.downl.lang, 'en')
        self.assertEqual(self.downl.site_url, 'http://en.ninemanga.com')

    def test_search(self):
        """Tests :meth:`smd.downloader.NineManga.search` function."""
        results = self.downl.search('naruto')
        with open(os.path.join(self.data_dir, 'search.json')) as data_fh:
            exp_res = [tuple(l) for l in json.load(data_fh)]
        self.assertEqual(results, exp_res)

    def test_get_chapters(self):
        """Tests :meth:`smd.downloader.NineManga.get_chapters` function."""
        chapters = self.downl.get_chapters('mangas/naruto1_warning.html')
        with open(os.path.join(self.data_dir, 'get_chapters.json')) as data_fh:
            exp_chaps = [tuple(l) for l in json.load(data_fh)]
        self.assertEqual(chapters, exp_chaps)

    def test_get_images(self):
        """Tests :meth:`smd.downloader.NineManga.get_images` function."""
        site_url = self.downl.site_url
        images_pages = self.downl.get_images(
            'image_pages/naruto1_ch1_img1.html')
        with open(os.path.join(self.data_dir, 'get_images.json')) as data_fh:
            exp_pages = [site_url+link for link in json.load(data_fh)]
        self.assertEqual(images_pages, exp_pages)

    def test_get_image(self):
        """Tests :meth:`smd.downloader.NineManga.get_image` function."""
        with open(os.path.join(self.data_dir, 'get_image.json')) as data_fh:
            exp_imgs = json.load(data_fh)
        for url, exp_img in exp_imgs.items():
            with self.subTest(exp_img=exp_img):
                image = self.downl.get_image(url)
                self.assertEqual(image, exp_img)


class TestHeavenManga(unittest.TestCase):

    """Tests :class:`smd.downloader.HeavenManga` class."""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.join(TEST_DIR, 'heavenmanga')
        cls.data_dir = os.path.join(DATA_DIR, 'heavenmanga')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = downloader.HeavenManga()
        cls.downl.get = cls.get

    @classmethod
    def tearDownClass(cls):
        cls.downl.logger.handlers[0].close()

    @classmethod
    def get(cls, url):
        """Method used to override the :meth:`smd.downloader.Downloader.get`
        method to emulate online connection."""
        search_url = TestHeavenManga.downl.site_url+'/buscar/'
        if url.startswith(search_url):
            data_name = os.path.join('search', url.replace(search_url, ''))
        else:
            data_name = url
        path = os.path.join(TestHeavenManga.data_dir, data_name)
        with open(path) as file_handler:
            return file_handler.read()

    def test_init(self):
        """Tests :meth:`smd.downloader.HeavenManga.__init__` function."""
        self.assertEqual(self.downl.name, 'heavenmanga')
        self.assertEqual(self.downl.lang, 'es')
        self.assertEqual(self.downl.site_url, 'http://heavenmanga.com')

    def test_search(self):
        """Tests :meth:`smd.downloader.HeavenManga.search` function."""
        results = self.downl.search('naruto')
        with open(os.path.join(self.data_dir, 'search.json')) as data_fh:
            exp_res = [tuple(l) for l in json.load(data_fh)]
        self.assertEqual(results, exp_res)

    def test_get_chapters(self):
        """Tests :meth:`smd.downloader.HeavenManga.get_chapters` function."""
        chapters = self.downl.get_chapters('mangas/naruto1.html')
        with open(os.path.join(self.data_dir, 'get_chapters.json')) as data_fh:
            exp_chaps = [tuple(l) for l in json.load(data_fh)]
        self.assertEqual(chapters, exp_chaps)

    def test_get_images(self):
        """Tests :meth:`smd.downloader.HeavenManga.get_images` function."""
        images_pages = self.downl.get_images('chapter_pages/naruto1_ch1.html')
        with open(os.path.join(self.data_dir, 'get_images.json')) as data_fh:
            exp_pages = json.load(data_fh)
        self.assertEqual(images_pages, exp_pages)

    def test_get_image(self):
        """Tests :meth:`smd.downloader.HeavenManga.get_image` function."""
        with open(os.path.join(self.data_dir, 'get_image.json')) as data_fh:
            exp_imgs = json.load(data_fh)
        for url, exp_img in exp_imgs.items():
            with self.subTest(exp_img=exp_img):
                image = self.downl.get_image(url)
                self.assertEqual(image, exp_img)


class TestMangaReader(unittest.TestCase):

    """Tests :class:`smd.downloader.MangaReader` class."""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.join(TEST_DIR, 'mangareader')
        cls.data_dir = os.path.join(DATA_DIR, 'mangareader')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = downloader.MangaReader()
        cls.downl.get = cls.get

    @classmethod
    def tearDownClass(cls):
        cls.downl.logger.handlers[0].close()

    @classmethod
    def get(cls, url, data=None):
        """Method used to override the :meth:`smd.downloader.Downloader.get`
        method to emulate online connection."""
        if url.endswith('/actions/search/'):
            data_name = 'search/'+data['q']+'.html'
        else:
            data_name = url
        path = os.path.join(TestMangaReader.data_dir, data_name)
        with open(path) as file_handler:
            return file_handler.read()

    def test_init(self):
        """Tests :meth:`smd.downloader.MangaReader.__init__` function."""
        self.assertEqual(self.downl.name, 'mangareader')
        self.assertEqual(self.downl.lang, 'en')
        self.assertEqual(self.downl.site_url, 'https://www.mangareader.net')

    def test_search(self):
        """Tests :meth:`smd.downloader.MangaReader.search` function."""
        site_url = self.downl.site_url
        results = self.downl.search('naruto')
        with open(os.path.join(self.data_dir, 'search.json')) as data_fh:
            exp_res = [(l[0], site_url+'/'+l[1]) for l in json.load(data_fh)]
        self.assertEqual(results, exp_res)

    def test_get_chapters(self):
        """Tests :meth:`smd.downloader.MangaReader.get_chapters` function."""
        site_url = self.downl.site_url
        chapters = self.downl.get_chapters('mangas/naruto1.html')
        with open(os.path.join(self.data_dir, 'get_chapters.json')) as data_fh:
            exp_chaps = [(l[0], site_url+'/'+l[1]) for l in json.load(data_fh)]
        self.assertEqual(chapters, exp_chaps)

    def test_get_images(self):
        """Tests :meth:`smd.downloader.MangaReader.get_images` function."""
        site_url = self.downl.site_url
        images_pages = self.downl.get_images(
            'image_pages/naruto1_ch1_img1.html')
        with open(os.path.join(self.data_dir, 'get_images.json')) as data_fh:
            exp_pages = [site_url+'/'+l for l in json.load(data_fh)]
        self.assertEqual(images_pages, exp_pages)

    def test_get_image(self):
        """Tests :meth:`smd.downloader.MangaReader.get_image` function."""
        with open(os.path.join(self.data_dir, 'get_image.json')) as data_fh:
            exp_imgs = json.load(data_fh)
        for url, exp_img in exp_imgs.items():
            with self.subTest(exp_img=exp_img):
                image = self.downl.get_image(url)
                self.assertEqual(image, exp_img)


class TestMangaAll(unittest.TestCase):

    """Tests :class:`smd.downloader.MangaAll` class."""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.join(TEST_DIR, 'mangaall')
        cls.data_dir = os.path.join(DATA_DIR, 'mangaall')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = downloader.MangaAll()
        cls.downl.get = cls.get

    @classmethod
    def tearDownClass(cls):
        cls.downl.logger.handlers[0].close()

    @classmethod
    def get(cls, url, data=None):
        """Method used to override the :meth:`smd.downloader.Downloader.get`
        method to emulate online connection."""
        if url.endswith('/search/'):
            data_name = 'search/'+data['q']+'.html'
        else:
            data_name = url
        path = os.path.join(TestMangaAll.data_dir, data_name)
        with open(path) as file_handler:
            return file_handler.read()

    def test_init(self):
        """Tests :meth:`smd.downloader.MangaAll.__init__` function."""
        self.assertEqual(self.downl.name, 'mangaall')
        self.assertEqual(self.downl.lang, 'en')
        self.assertEqual(self.downl.site_url, 'http://mangaall.net')

    def test_search(self):
        """Tests :meth:`smd.downloader.MangaAll.search` function."""
        results = self.downl.search('naruto')
        with open(os.path.join(self.data_dir, 'search.json')) as data_fh:
            exp_res = [tuple(l) for l in json.load(data_fh)]
        self.assertEqual(results, exp_res)

    def test_get_chapters(self):
        """Tests :meth:`smd.downloader.MangaAll.get_chapters` function."""
        chapters = self.downl.get_chapters('mangas/naruto1.html')
        with open(os.path.join(self.data_dir, 'get_chapters.json')) as data_fh:
            exp_chaps = [tuple(l) for l in json.load(data_fh)]
        self.assertEqual(chapters, exp_chaps)

    def test_get_images(self):
        """Tests :meth:`smd.downloader.MangaAll.get_images` function."""
        images_pages = self.downl.get_images(
            'image_pages/naruto1_ch1_img1.html')
        with open(os.path.join(self.data_dir, 'get_images.json')) as data_fh:
            exp_pages = json.load(data_fh)
        self.assertEqual(images_pages, exp_pages)

    def test_get_image(self):
        """Tests :meth:`smd.downloader.MangaAll.get_image` function."""
        with open(os.path.join(self.data_dir, 'get_image.json')) as data_fh:
            exp_imgs = json.load(data_fh)
        for url, exp_img in exp_imgs.items():
            with self.subTest(exp_img=exp_img):
                image = self.downl.get_image(url)
                self.assertEqual(image, exp_img)


class TestMangaDoor(unittest.TestCase):

    """Tests :class:`smd.downloader.MangaDoor` class."""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.join(TEST_DIR, 'mangadoor')
        cls.data_dir = os.path.join(DATA_DIR, 'mangadoor')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = downloader.MangaDoor()
        cls.downl.get = cls.get

    @classmethod
    def tearDownClass(cls):
        cls.downl.logger.handlers[0].close()

    @classmethod
    def get(cls, url, data=None, method='GET', xhr=False):
        """Method used to override the :meth:`smd.downloader.Downloader.get`
        method to emulate online connection."""
        if url.endswith('/search/'):
            data_name = 'search/'+data['query']+'.json'
        else:
            data_name = url
        path = os.path.join(TestMangaDoor.data_dir, data_name)
        with open(path) as file_handler:
            return file_handler.read()

    def test_init(self):
        """Tests :meth:`smd.downloader.MangaDoor.__init__` function."""
        self.assertEqual(self.downl.name, 'mangadoor')
        self.assertEqual(self.downl.lang, 'es')
        self.assertEqual(self.downl.site_url, 'http://mangadoor.com')

    def test_search(self):
        """Tests :meth:`smd.downloader.MangaDoor.search` function."""
        site_url = self.downl.site_url
        results = self.downl.search('naruto')
        with open(os.path.join(self.data_dir, 'search.json')) as data_fh:
            exp_res = [(l[0], site_url+'/'+l[1]) for l in json.load(data_fh)]
        self.assertEqual(results, exp_res)

    def test_get_chapters(self):
        """Tests :meth:`smd.downloader.MangaDoor.get_chapters` function."""
        chapters = self.downl.get_chapters('mangas/naruto1.html')
        with open(os.path.join(self.data_dir, 'get_chapters.json')) as data_fh:
            exp_chaps = [tuple(l) for l in json.load(data_fh)]
        self.assertEqual(chapters, exp_chaps)

    def test_get_images(self):
        """Tests :meth:`smd.downloader.MangaDoor.get_images` function."""
        chap_url = 'image_pages/naruto1_ch1_img1.html'
        images_pages = self.downl.get_images(chap_url)
        with open(os.path.join(self.data_dir, 'get_images.json')) as data_fh:
            exp_pages = [chap_url+'/'+l for l in json.load(data_fh)]
        self.assertEqual(images_pages, exp_pages)

    def test_get_image(self):
        """Tests :meth:`smd.downloader.MangaDoor.get_image` function."""
        with open(os.path.join(self.data_dir, 'get_image.json')) as data_fh:
            exp_imgs = json.load(data_fh)
        for url, exp_img in exp_imgs.items():
            with self.subTest(exp_img=exp_img):
                image = self.downl.get_image(url)
                self.assertEqual(image, exp_img)


class TestMangaNelo(unittest.TestCase):

    """Tests :class:`smd.downloader.MangaNelo` class."""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.join(TEST_DIR, 'manganelo')
        cls.data_dir = os.path.join(DATA_DIR, 'manganelo')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = downloader.MangaNelo()
        cls.downl.get = cls.get

    @classmethod
    def tearDownClass(cls):
        cls.downl.logger.handlers[0].close()

    @classmethod
    def get(cls, url, data=None, method='GET', xhr=False):
        """Method used to override the :meth:`smd.downloader.Downloader.get`
        method to emulate online connection."""
        if url.endswith('/home_json_search/'):
            data_name = 'search/'+data['searchword']+'.json'
        else:
            data_name = url
        path = os.path.join(TestMangaNelo.data_dir, data_name)
        with open(path) as file_handler:
            return file_handler.read()

    def test_init(self):
        """Tests :meth:`smd.downloader.MangaNelo.__init__` function."""
        self.assertEqual(self.downl.name, 'manganelo')
        self.assertEqual(self.downl.lang, 'en')
        self.assertEqual(self.downl.site_url, 'https://manganelo.com')

    def test_search(self):
        """Tests :meth:`smd.downloader.MangaNelo.search` function."""
        site_url = self.downl.site_url
        results = self.downl.search('naruto')
        with open(os.path.join(self.data_dir, 'search.json')) as data_fh:
            exp_res = [(l[0], site_url+'/'+l[1]) for l in json.load(data_fh)]
        self.assertEqual(results, exp_res)

    def test_get_chapters(self):
        """Tests :meth:`smd.downloader.MangaNelo.get_chapters` function."""
        chapters = self.downl.get_chapters('mangas/naruto1.html')
        with open(os.path.join(self.data_dir, 'get_chapters.json')) as data_fh:
            exp_chaps = [tuple(l) for l in json.load(data_fh)]
        self.assertEqual(chapters, exp_chaps)

    def test_get_images(self):
        """Tests :meth:`smd.downloader.MangaNelo.get_images` function."""
        chap_url = 'image_pages/naruto1_ch1.html'
        images_pages = self.downl.get_images(chap_url)
        with open(os.path.join(self.data_dir, 'get_images.json')) as data_fh:
            exp_pages = json.load(data_fh)
        self.assertEqual(images_pages, exp_pages)


class TestMangaHere(unittest.TestCase):

    """Tests :class:`smd.downloader.MangaHere` class."""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.join(TEST_DIR, 'mangahere')
        cls.data_dir = os.path.join(DATA_DIR, 'mangahere')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = downloader.MangaHere()
        cls.downl.get = cls.get

    @classmethod
    def tearDownClass(cls):
        cls.downl.logger.handlers[0].close()

    @classmethod
    def get(cls, url, data=None, method='GET', xhr=False):
        """Method used to override the :meth:`smd.downloader.Downloader.get`
        method to emulate online connection."""
        if url.endswith('/ajax/search.php'):
            data_name = 'search/'+data['query']+'.json'
        else:
            data_name = url
        path = os.path.join(TestMangaHere.data_dir, data_name)
        with open(path) as file_handler:
            return file_handler.read()

    def test_init(self):
        """Tests :meth:`smd.downloader.MangaHere.__init__` function."""
        self.assertEqual(self.downl.name, 'mangahere')
        self.assertEqual(self.downl.lang, 'en')
        self.assertEqual(self.downl.site_url, 'http://www.mangahere.cc')

    def test_search(self):
        """Tests :meth:`smd.downloader.MangaHere.search` function."""
        results = self.downl.search('naruto')
        with open(os.path.join(self.data_dir, 'search.json')) as data_fh:
            exp_res = [tuple(l) for l in json.load(data_fh)]
        self.assertEqual(results, exp_res)

    def test_get_chapters(self):
        """Tests :meth:`smd.downloader.MangaHere.get_chapters` function."""
        chapters = self.downl.get_chapters('mangas/naruto1.html')
        with open(os.path.join(self.data_dir, 'get_chapters.json')) as data_fh:
            exp_chaps = [tuple(l) for l in json.load(data_fh)]
        self.assertEqual(chapters, exp_chaps)

    def test_get_images(self):
        """Tests :meth:`smd.downloader.MangaHere.get_images` function."""
        chap_url = 'image_pages/naruto1_ch1_img1.html'
        images_pages = self.downl.get_images(chap_url)
        with open(os.path.join(self.data_dir, 'get_images.json')) as data_fh:
            exp_pages = json.load(data_fh)
        self.assertEqual(images_pages, exp_pages)

    def test_get_image(self):
        """Tests :meth:`smd.downloader.MangaHere.get_image` function."""
        with open(os.path.join(self.data_dir, 'get_image.json')) as data_fh:
            exp_imgs = json.load(data_fh)
        for url, exp_img in exp_imgs.items():
            with self.subTest(exp_img=exp_img):
                image = self.downl.get_image(url)
                self.assertEqual(image, exp_img)
