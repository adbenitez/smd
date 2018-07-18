# -*- coding: utf-8 -*-
'''Some basic offline tests'''

from io import StringIO
import json
import os
import sys
import unittest

from . import smd, empty_dir

ROOT = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = 'test_dir'


class Downloader(smd.Downloader):
    def __init__(self, name='downloader-test', lang='jp',
                 site_url='http://downloader-test.com'):
        smd.Downloader.__init__(self, name, lang, site_url)

    def get(self, url, data=None, method='GET', xhr=False, decode=True):
        path = os.path.join(ROOT, 'data', 'downloader', url)
        with open(path, 'rb') as f:
            if decode:
                return f.read().decode(errors='ignore')
            else:
                return f.read()

    def search(self, manga):
        return [('Naruto', 'mangas/naruto1.html'),
                ('Naruto: OneShot', 'mangas/naruto2.html'),
                (r'@#$=\([¿¡PROBLEMATIC PATH NARUTO!?])/%^&*',
                 'mangas/naruto3.html')]

    def get_chapters(self, manga_url):
        return [('chapter 1', 'image_pages/naruto1_ch1_img1.html'),
                ('chapter 2', 'image_pages/naruto1_ch2_img1.html'),
                ('chapter 3', 'image_pages/naruto1_ch3_img1.html'),
                ('chapter 4', 'image_pages/naruto1_ch4_img1.html'),
                ('chapter 5', 'image_pages/naruto1_ch5_img1.html'),
                ('chapter 6', 'image_pages/naruto1_ch6_img1.html'),
                ('chapter 7', 'image_pages/naruto1_ch7_img1.html'),
                ('chapter 8', 'image_pages/naruto1_ch8_img1.html'),
                ('chapter 9', 'image_pages/naruto1_ch9_img1.html'),
                ('chapter 10', 'image_pages/naruto1_ch10_img1.html')]

    def get_images(self, chapter_url):
        return ['image_pages/naruto1_ch1_img1.html',
                'image_pages/naruto1_ch1_img2.html',
                'image_pages/naruto1_ch1_img3.html']

    def get_image(self, image_url):
        image_url = image_url.replace('image_pages/naruto1_ch1_', '')
        return 'images/'+image_url.replace('.html', '.jpeg')


class TestSmdCli(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stdin = sys.stdin
        cls.test_dir = os.path.abspath(TEST_DIR)
        cls.data_dir = os.path.join(ROOT, 'data', 'smd_cli')
        os.mkdir(cls.test_dir)

    @classmethod
    def tearDownClass(cls):
        sys.stdin = cls.stdin
        os.rmdir(cls.test_dir)

    def tearDown(self):
        sys.stdin.close()
        empty_dir(self.test_dir)

    def test_select_downloader(self):
        downloaders = [Downloader('d{}'.format(i)) for i in range(1, 4)]
        i = 2
        exp_d = downloaders[i-1]
        sys.stdin = StringIO("{}\n{}\n{}".format(len(downloaders)+1, -1, i))
        smd.select_downloader(downloaders)
        for d in downloaders:
            d.logger.handlers[0].close()
        self.assertIs(downloaders[0], exp_d)

    def test_select_lang(self):
        langs = 'es en de'.split()
        i = 1
        stdin = "{}\n{}\n{}".format(len(langs)+1, -1, i)
        sys.stdin = StringIO(stdin)
        lang = smd.select_lang(langs)
        self.assertEqual(lang, langs[i-1])

    def test_list_downloaders(self):
        langs = ['en', 'es', 'de']
        downloaders = [Downloader('d{}'.format(i), lang)
                       for i, lang in enumerate(langs, 1)]
        smd.list_downloaders(downloaders)
        for d in downloaders:
            d.logger.handlers[0].close()

    def test_create_config_folder(self):
        exp_dir = os.path.join(os.path.expanduser('~'), 'smd')
        empty_dir(exp_dir)
        os.rmdir(exp_dir)
        config_dir = smd.create_config_folder()
        self.assertEqual(config_dir, exp_dir)
        self.assertTrue(os.path.isdir(exp_dir))


class TestDownloader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        smd.Downloader.logfile = os.path.abspath('smd.log')
        cls.test_dir = os.path.abspath(TEST_DIR)
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = Downloader()

    @classmethod
    def tearDownClass(cls):
        parent_dir = os.path.dirname(cls.test_dir)
        os.chdir(parent_dir)
        os.rmdir(cls.test_dir)

    def tearDown(self):
        sys.stdin.close()
        empty_dir(self.test_dir)

    def test_init(self):
        site_url = 'http://downloader-test.com'
        self.assertEqual(self.downl.name, 'downloader-test')
        self.assertEqual(self.downl.lang, 'jp')
        self.assertEqual(self.downl.site_url, site_url)

    def test_str(self):
        name = 'downloader-test'
        self.assertEqual(str(self.downl), name)

    def test_select_manga(self):
        i = 1
        mangas = self.downl.search('naruto')
        sys.stdin = StringIO("{}\n{}\n{}".format(len(mangas)+1, -1, i))
        manga = self.downl.select_manga(mangas)
        exp_manga = mangas[i-1]
        self.assertEqual(manga, exp_manga)

    def test_mkdir(self):
        sys.stdin = StringIO('td\ntd\ntd2\ntd3')
        dirs = ['test\\/mkdir', 'test[>:-/]mkdir']
        for d in dirs:
            self.downl._mkdir('.', d)
        test_dir = 'test_mkdir'
        self.downl._mkdir('.', test_dir)
        self.assertTrue(os.path.isdir(test_dir))

    def test_select_chapters(self):
        chapters = self.downl.get_chapters('')
        selectors = ['1:10', '-1', '!-3', '1,3,5', ':5, !3, 7:, !9:10']
        exp_values = [set(chapters[0:10]), set([chapters[-1]]),
                      set(chapters) - set([chapters[-3]]),
                      set([chapters[0], chapters[2], chapters[4]]),
                      set(chapters[:5]+chapters[6:]) -
                      set([chapters[2]]+chapters[8:10])]
        for selector, exp in zip(selectors, exp_values):
            with self.subTest(selector=selector):
                selec = self.downl._select_chapters(chapters, selector)
                self.assertEqual(selec, exp)

    @unittest.expectedFailure
    def test_fail_select_chapters(self):
        selectors = ['1:0', 'inject_code()', '1000']
        for selector in selectors:
            with self.subTest(selector=selector):
                self.downl._select_chapters([], selector)

    def test_download_img(self):
        self.downl.download_img('images/img1.jpeg', 'test_01')
        with open('test_01.jpeg', 'rb') as fh:
            img = fh.read()
        exp_img = self.downl.get('images/img1.jpeg', decode=False)
        self.assertEqual(img, exp_img)

    def test_download(self):
        sys.stdin = StringIO('3\nPROBLEMATIC NARUTO')
        self.assertTrue(self.downl.download('naruto', '1:3'))

    def test_get_json(self):
        data = self.downl.get_json('test.json')
        exp_data = json.loads(self.downl.get('test.json'))
        self.assertEqual(data, exp_data)


class TestNineManga(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        smd.Downloader.logfile = os.path.abspath('smd.log')
        cls.test_dir = os.path.abspath(TEST_DIR)
        cls.data_dir = os.path.join(ROOT, 'data', 'ninemanga')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = smd.NineManga('en')
        cls.downl.get = cls.get

    @classmethod
    def tearDownClass(cls):
        parent_dir = os.path.dirname(cls.test_dir)
        os.chdir(parent_dir)
        os.rmdir(cls.test_dir)

    def tearDown(self):
        empty_dir(self.test_dir)

    def get(url, data=None):
        if url.endswith('/search/'):
            data_name = 'search/'+data['wd']+'.html'
        else:
            data_name = url
        path = os.path.join(TestNineManga.data_dir, data_name)
        with open(path) as f:
            return f.read()

    def test_init(self):
        self.assertEqual(self.downl.name, 'ninemanga-en')
        self.assertEqual(self.downl.lang, 'en')
        self.assertEqual(self.downl.site_url, 'http://en.ninemanga.com')

    def test_search(self):
        results = self.downl.search('naruto')
        exp_res = [('Naruto', 'mangas/naruto1.html'),
                   ('Naruto: OneShot', 'mangas/naruto2.html'),
                   (r'@#$=\([¿¡PROBLEMATIC PATH NARUTO!?])/%^&*',
                    'mangas/naruto3.html')]
        self.assertEqual(results, exp_res)

    def test_get_chapters(self):
        chapters = self.downl.get_chapters('mangas/naruto1_warning.html')
        exp_chaps = [('chapter 1', 'image_pages/naruto1_ch1_img1.html'),
                     ('chapter 2', 'image_pages/naruto1_ch2_img1.html'),
                     ('chapter 3', 'image_pages/naruto1_ch3_img1.html')]
        self.assertEqual(chapters, exp_chaps)

    def test_get_images(self):
        site_url = self.downl.site_url
        images_pages = self.downl.get_images(
            'image_pages/naruto1_ch1_img1.html')
        exp_pages = [site_url+'/naruto1_ch1_img1.html',
                     site_url+'/naruto1_ch1_img2.html',
                     site_url+'/naruto1_ch1_img3.html']
        self.assertEqual(images_pages, exp_pages)

    def test_get_image(self):
        for i in range(1, 4):
            with self.subTest(i=i):
                url = 'image_pages/naruto1_ch1_img{}.html'.format(i)
                image = self.downl.get_image(url)
                self.assertEqual(image, 'images/img{}.jpeg'.format(i))


class TestHeavenManga(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        smd.Downloader.logfile = os.path.abspath('smd.log')
        cls.test_dir = os.path.abspath(TEST_DIR)
        cls.data_dir = os.path.join(ROOT, 'data', 'heavenmanga')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = smd.HeavenManga()
        cls.downl.get = cls.get

    @classmethod
    def tearDownClass(cls):
        parent_dir = os.path.dirname(cls.test_dir)
        os.chdir(parent_dir)
        os.rmdir(cls.test_dir)

    def tearDown(self):
        empty_dir(self.test_dir)

    def get(url):
        search_url = TestHeavenManga.downl.site_url+'/buscar/'
        if url.startswith(search_url):
            data_name = os.path.join('search', url.replace(search_url, ''))
        else:
            data_name = url
        path = os.path.join(TestHeavenManga.data_dir, data_name)
        with open(path) as f:
            return f.read()

    def test_init(self):
        self.assertEqual(self.downl.name, 'heavenmanga')
        self.assertEqual(self.downl.lang, 'es')
        self.assertEqual(self.downl.site_url, 'http://heavenmanga.com')

    def test_search(self):
        results = self.downl.search('naruto')
        exp_res = [('Naruto', 'mangas/naruto1.html'),
                   ('Naruto: OneShot', 'mangas/naruto2.html'),
                   ('Another Naruto Stuff!', 'mangas/naruto3.html')]
        self.assertEqual(results, exp_res)

    def test_get_chapters(self):
        chapters = self.downl.get_chapters('mangas/naruto1.html')
        exp_chaps = [('chapter 1', 'chapter_pages/naruto1_ch1.html'),
                     ('chapter 2', 'chapter_pages/naruto1_ch2.html'),
                     ('chapter 3', 'chapter_pages/naruto1_ch3.html')]
        self.assertEqual(chapters, exp_chaps)

    def test_get_images(self):
        images_pages = self.downl.get_images('chapter_pages/naruto1_ch1.html')
        exp_pages = ['image_pages/naruto1_ch1_img1.html',
                     'image_pages/naruto1_ch1_img2.html',
                     'image_pages/naruto1_ch1_img3.html']
        self.assertEqual(images_pages, exp_pages)

    def test_get_image(self):
        for i in range(1, 4):
            with self.subTest(i=i):
                url = 'image_pages/naruto1_ch1_img{}.html'.format(i)
                image = self.downl.get_image(url)
                self.assertEqual(image, 'images/img{}.jpeg'.format(i))


class TestMangaReader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        smd.Downloader.logfile = os.path.abspath('smd.log')
        cls.test_dir = os.path.abspath(TEST_DIR)
        cls.data_dir = os.path.join(ROOT, 'data', 'mangareader')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = smd.MangaReader()
        cls.downl.get = cls.get

    @classmethod
    def tearDownClass(cls):
        parent_dir = os.path.dirname(cls.test_dir)
        os.chdir(parent_dir)
        os.rmdir(cls.test_dir)

    def tearDown(self):
        empty_dir(self.test_dir)

    def get(url, data=None):
        if url.endswith('/actions/search/'):
            data_name = 'search/'+data['q']+'.html'
        else:
            data_name = url
        path = os.path.join(TestMangaReader.data_dir, data_name)
        with open(path) as f:
            return f.read()

    def test_init(self):
        self.assertEqual(self.downl.name, 'mangareader')
        self.assertEqual(self.downl.lang, 'en')
        self.assertEqual(self.downl.site_url, 'https://www.mangareader.net')

    def test_search(self):
        site_url = self.downl.site_url
        results = self.downl.search('naruto')
        exp_res = [('Naruto', site_url+'/mangas/naruto1.html'),
                   ('Naruto: OneShot', site_url+'/mangas/naruto2.html'),
                   (r'@#$=\([¿¡PROBLEMATIC PATH NARUTO!?])/%^&*',
                    site_url+'/mangas/naruto3.html')]
        self.assertEqual(results, exp_res)

    def test_get_chapters(self):
        site_url = self.downl.site_url
        chapters = self.downl.get_chapters('mangas/naruto1.html')
        exp_chaps = [('chapter 1',
                      site_url+'/image_pages/naruto1_ch1_img1.html'),
                     ('chapter 2',
                      site_url+'/image_pages/naruto1_ch2_img1.html'),
                     ('chapter 3',
                      site_url+'/image_pages/naruto1_ch3_img1.html')]
        self.assertEqual(chapters, exp_chaps)

    def test_get_images(self):
        site_url = self.downl.site_url
        images_pages = self.downl.get_images(
            'image_pages/naruto1_ch1_img1.html')
        exp_pages = [site_url+'/image_pages/naruto1_ch1_img1.html',
                     site_url+'/image_pages/naruto1_ch1_img2.html',
                     site_url+'/image_pages/naruto1_ch1_img3.html']
        self.assertEqual(images_pages, exp_pages)

    def test_get_image(self):
        for i in range(1, 4):
            with self.subTest(i=i):
                url = 'image_pages/naruto1_ch1_img{}.html'.format(i)
                image = self.downl.get_image(url)
                self.assertEqual(image, 'images/img{}.jpeg'.format(i))


class TestMangaAll(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        smd.Downloader.logfile = os.path.abspath('smd.log')
        cls.test_dir = os.path.abspath(TEST_DIR)
        cls.data_dir = os.path.join(ROOT, 'data', 'mangaall')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = smd.MangaAll()
        cls.downl.get = cls.get

    @classmethod
    def tearDownClass(cls):
        parent_dir = os.path.dirname(cls.test_dir)
        os.chdir(parent_dir)
        os.rmdir(cls.test_dir)

    def tearDown(self):
        empty_dir(self.test_dir)

    def get(url, data=None):
        if url.endswith('/search/'):
            data_name = 'search/'+data['q']+'.html'
        else:
            data_name = url
        path = os.path.join(TestMangaAll.data_dir, data_name)
        with open(path) as f:
            return f.read()

    def test_init(self):
        self.assertEqual(self.downl.name, 'mangaall')
        self.assertEqual(self.downl.lang, 'en')
        self.assertEqual(self.downl.site_url, 'http://mangaall.net')

    def test_search(self):
        results = self.downl.search('naruto')
        exp_res = [('Naruto', 'mangas/naruto1.html'),
                   ('Naruto: OneShot', 'mangas/naruto2.html'),
                   (r'@#$=\([¿¡PROBLEMATIC PATH NARUTO!?])/%^&*',
                    'mangas/naruto3.html')]
        self.assertEqual(results, exp_res)

    def test_get_chapters(self):
        chapters = self.downl.get_chapters('mangas/naruto1.html')
        exp_chaps = [('chapter 1', 'image_pages/naruto1_ch1_img1.html'),
                     ('chapter 2', 'image_pages/naruto1_ch2_img1.html'),
                     ('chapter 3', 'image_pages/naruto1_ch3_img1.html')]
        self.assertEqual(chapters, exp_chaps)

    def test_get_images(self):
        images_pages = self.downl.get_images(
            'image_pages/naruto1_ch1_img1.html')
        exp_pages = ['image_pages/naruto1_ch1_img1.html?page=1',
                     'image_pages/naruto1_ch1_img1.html?page=2',
                     'image_pages/naruto1_ch1_img1.html?page=3']
        self.assertEqual(images_pages, exp_pages)

    def test_get_image(self):
        for i in range(1, 4):
            with self.subTest(i=i):
                url = 'image_pages/naruto1_ch1_img{}.html'.format(i)
                image = self.downl.get_image(url)
                self.assertEqual(image, 'images/img{}.jpeg'.format(i))


class TestMangaDoor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        smd.Downloader.logfile = os.path.abspath('smd.log')
        cls.test_dir = os.path.abspath(TEST_DIR)
        cls.data_dir = os.path.join(ROOT, 'data', 'mangadoor')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = smd.MangaDoor()
        cls.downl.get = cls.get

    @classmethod
    def tearDownClass(cls):
        parent_dir = os.path.dirname(cls.test_dir)
        os.chdir(parent_dir)
        os.rmdir(cls.test_dir)

    def tearDown(self):
        empty_dir(self.test_dir)

    def get(url, data=None, method='GET', xhr=False):
        if url.endswith('/search/'):
            data_name = 'search/'+data['query']+'.json'
        else:
            data_name = url
        path = os.path.join(TestMangaDoor.data_dir, data_name)
        with open(path) as f:
            return f.read()

    def test_init(self):
        self.assertEqual(self.downl.name, 'mangadoor')
        self.assertEqual(self.downl.lang, 'es')
        self.assertEqual(self.downl.site_url, 'http://mangadoor.com')

    def test_search(self):
        site_url = self.downl.site_url
        results = self.downl.search('naruto')
        exp_res = [('Naruto', site_url+'/manga/naruto1.html'),
                   ('Naruto: OneShot', site_url+'/manga/naruto2.html'),
                   (r'@#$=\([¿¡PROBLEMATIC PATH NARUTO!?])/%^&*',
                    site_url+'/manga/naruto3.html')]
        self.assertEqual(results, exp_res)

    def test_get_chapters(self):
        chapters = self.downl.get_chapters('mangas/naruto1.html')
        exp_chaps = [('chapter 1', 'image_pages/naruto1_ch1_img1.html'),
                     ('chapter 2', 'image_pages/naruto1_ch2_img1.html'),
                     ('chapter 3', 'image_pages/naruto1_ch3_img1.html')]
        self.assertEqual(chapters, exp_chaps)

    def test_get_images(self):
        chap_url = 'image_pages/naruto1_ch1_img1.html'
        images_pages = self.downl.get_images(chap_url)
        exp_pages = [chap_url+'/image_pages/naruto1_ch1_img1.html',
                     chap_url+'/image_pages/naruto1_ch1_img2.html',
                     chap_url+'/image_pages/naruto1_ch1_img3.html']
        self.assertEqual(images_pages, exp_pages)

    def test_get_image(self):
        for i in range(1, 4):
            with self.subTest(i=i):
                url = 'image_pages/naruto1_ch1_img{}.html'.format(i)
                image = self.downl.get_image(url)
                self.assertEqual(image, 'images/img{}.jpeg'.format(i))


class TestMangaNelo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        smd.Downloader.logfile = os.path.abspath('smd.log')
        cls.test_dir = os.path.abspath(TEST_DIR)
        cls.data_dir = os.path.join(ROOT, 'data', 'manganelo')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = smd.MangaNelo()
        cls.downl.get = cls.get

    @classmethod
    def tearDownClass(cls):
        parent_dir = os.path.dirname(cls.test_dir)
        os.chdir(parent_dir)
        os.rmdir(cls.test_dir)

    def tearDown(self):
        empty_dir(self.test_dir)

    def get(url, data=None, method='GET', xhr=False):
        if url.endswith('/home_json_search/'):
            data_name = 'search/'+data['searchword']+'.json'
        else:
            data_name = url
        path = os.path.join(TestMangaNelo.data_dir, data_name)
        with open(path) as f:
            return f.read()

    def test_init(self):
        self.assertEqual(self.downl.name, 'manganelo')
        self.assertEqual(self.downl.lang, 'en')
        self.assertEqual(self.downl.site_url, 'https://manganelo.com')

    def test_search(self):
        site_url = self.downl.site_url
        results = self.downl.search('naruto')
        exp_res = [('Naruto', site_url+'/manga/naruto1.html'),
                   ('Naruto: OneShot', site_url+'/manga/naruto2.html'),
                   (r'@#$=\([¿¡PROBLEMATIC PATH NARUTO!?])/%^&*',
                    site_url+'/manga/naruto3.html')]
        self.assertEqual(results, exp_res)

    def test_get_chapters(self):
        chapters = self.downl.get_chapters('mangas/naruto1.html')
        exp_chaps = [('chapter 1', 'image_pages/naruto1_ch1.html'),
                     ('chapter 2',
                      'https://image_pages/naruto1_ch2.html'),
                     ('chapter 3', 'image_pages/naruto1_ch3.html')]
        self.assertEqual(chapters, exp_chaps)

    def test_get_images(self):
        chap_url = 'image_pages/naruto1_ch1.html'
        images_pages = self.downl.get_images(chap_url)
        exp_pages = ['images/img1.jpeg',
                     'images/img2.jpeg',
                     'images/img3.jpeg']
        self.assertEqual(images_pages, exp_pages)


class TestMangaHere(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        smd.Downloader.logfile = os.path.abspath('smd.log')
        cls.test_dir = os.path.abspath(TEST_DIR)
        cls.data_dir = os.path.join(ROOT, 'data', 'mangahere')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.downl = smd.MangaHere()
        cls.downl.get = cls.get

    @classmethod
    def tearDownClass(cls):
        parent_dir = os.path.dirname(cls.test_dir)
        os.chdir(parent_dir)
        os.rmdir(cls.test_dir)

    def tearDown(self):
        empty_dir(self.test_dir)

    def get(url, data=None, method='GET', xhr=False):
        if url.endswith('/ajax/search.php'):
            data_name = 'search/'+data['query']+'.json'
        else:
            data_name = url
        path = os.path.join(TestMangaHere.data_dir, data_name)
        with open(path) as f:
            return f.read()

    def test_init(self):
        self.assertEqual(self.downl.name, 'mangahere')
        self.assertEqual(self.downl.lang, 'en')
        self.assertEqual(self.downl.site_url, 'http://www.mangahere.cc')

    def test_search(self):
        results = self.downl.search('naruto')
        exp_res = [('Naruto', 'http://manga/naruto1.html'),
                   ('Naruto: OneShot', 'http://manga/naruto2.html'),
                   (r'@#$=\([¿¡PROBLEMATIC PATH NARUTO!?])/%^&*',
                    'http://manga/naruto3.html')]
        self.assertEqual(results, exp_res)

    def test_get_chapters(self):
        chapters = self.downl.get_chapters('mangas/naruto1.html')
        exp_chaps = [('chapter 1', 'http://image_pages/naruto1_ch1_img1.html'),
                     ('chapter 2', 'http://image_pages/naruto1_ch2_img1.html'),
                     ('chapter 3', 'http://image_pages/naruto1_ch3_img1.html')]
        self.assertEqual(chapters, exp_chaps)

    def test_get_images(self):
        chap_url = 'image_pages/naruto1_ch1_img1.html'
        images_pages = self.downl.get_images(chap_url)
        exp_pages = ['http://image_pages/naruto1_ch1_img1.html',
                     'http://image_pages/naruto1_ch1_img2.html',
                     'http://image_pages/naruto1_ch1_img3.html']
        self.assertEqual(images_pages, exp_pages)

    def test_get_image(self):
        for i in range(1, 4):
            with self.subTest(i=i):
                url = 'image_pages/naruto1_ch1_img{}.html'.format(i)
                image = self.downl.get_image(url)
                self.assertEqual(image, 'images/img{}.jpeg'.format(i))


if __name__ == '__main__':
    unittest.main()
