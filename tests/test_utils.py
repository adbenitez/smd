# -*- coding: utf-8 -*-
"""
.. module:: tests.test_utils

Offline tests for the :mod:`smd.util` module.

"""

from io import StringIO
import json
import logging
import os
import shutil
import sys
import unittest

from bs4 import BeautifulSoup

import smd.downloader as downloader
import smd.utils as utils

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, 'data', 'util')
TEST_DIR = os.path.join(os.path.dirname(ROOT), 'test_utils_temp')


def setUpModule():
    """Creates a temporal directory where the tests are run."""
    os.mkdir(TEST_DIR)


def tearDownModule():
    """Removes the temporal tests directory."""
    shutil.rmtree(TEST_DIR)


class Downloader(downloader.Downloader):

    """A basic implementation of the abstract class
    :class:`smd.downloader.Downloader`"""

    def __init__(self, name='util-test', lang='en',
                 site_url='http://util-test.com'):
        self._init_logger = lambda: True
        downloader.Downloader.__init__(self, name, lang, site_url)
        self.logger = logging

    def get_chapters(self, manga_url):
        pass

    def get_images(self, chap_url):
        pass

    def search(self, manga):
        pass


class TestChapter(unittest.TestCase):

    """Tests :class:`smd.utils.Chapter` class."""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.join(TEST_DIR, 'chapter')
        cls.data_dir = os.path.join(DATA_DIR, 'chapter')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)

    def test_init(self):
        """Tests :meth:`smd.utils.Chapter.__init__` function."""
        path = os.path.join(self.test_dir, 'TestChapter')
        title = 'Test Chapter'
        url = 'http://test-chapter.com'
        chap = utils.Chapter(path, title, url)
        self.assertEqual(chap.path, path)
        self.assertEqual(chap['title'], title)
        self.assertEqual(chap['url'], url)
        self.assertEqual(chap['current'], -1)
        self.assertEqual(chap['images'], [])

    def test_str(self):
        """Tests :meth:`smd.utils.Chapter.__str__` function."""
        title = 'test chapter'
        chap = utils.Chapter(self.test_dir, title=title)
        self.assertEqual(str(chap), title)

    def test_repr(self):
        """Tests :meth:`smd.utils.Chapter.__repr__` function."""
        title = 'test chapter'
        url = 'http://chapter-test.com'
        current = -1
        chap = utils.Chapter('path', title, url)
        exp_repr = '({}, {}, {})'.format(title, url, current)
        self.assertEqual(repr(chap), exp_repr)

    def test_from_folder(self):
        """Tests :meth:`smd.utils.Chapter.from_folder` function."""
        chap_dir = os.path.join(self.data_dir, 'chap1')
        chap = utils.Chapter.from_folder(chap_dir)
        self.assertEqual(chap['title'], 'chapter 1')
        self.assertEqual(chap['url'], 'image_pages/naruto1_ch1_img1.html')
        self.assertEqual(chap['current'], 3)
        self.assertEqual(len(chap['images']), 3)

    def test_is_chapter(self):
        """Tests :meth:`smd.utils.Chapter.is_chapter` function."""
        chap_dir = os.path.join(self.data_dir, 'chap1')
        self.assertTrue(utils.Chapter.is_chapter(chap_dir))

    def test_save_data(self):
        """Tests :meth:`smd.utils.Chapter.save_data` function."""
        utils.Chapter(self.test_dir).save_data()
        self.assertTrue(os.path.isfile(utils.Chapter._filename))


class TestConfig(unittest.TestCase):

    """Tests :class:`smd.utils.Config` class."""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.join(TEST_DIR, 'config')
        cls.cfg_path = os.path.join(cls.test_dir, 'smd.cfg')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)

    def tearDown(self):
        if os.path.exists(self.cfg_path):
            os.remove(self.cfg_path)

    def test_init(self):
        """Tests :meth:`smd.utils.Config.__init__` function."""
        cfg = utils.Config(self.cfg_path)
        self.assertFalse(os.path.exists(self.cfg_path))
        self.assertEqual(cfg.path, self.cfg_path)
        cfg['test'] = 'true'
        self.assertEqual(cfg['test'], 'true')
        with self.assertRaises(KeyError):
            cfg['bad_key']

    def test_exists(self):
        """Tests :meth:`smd.utils.Config.exists` function."""
        cfg = utils.Config(self.cfg_path)
        self.assertFalse(cfg.exists())
        with open(self.cfg_path, 'w') as fd:
            fd.write('[DEFAULT]\ntest=true\n\n')
        self.assertTrue(cfg.exists())

    def test_load(self):
        """Tests :meth:`smd.utils.Config.load` function."""
        cfg = utils.Config(self.cfg_path)
        self.assertFalse(cfg.load())
        with open(self.cfg_path, 'w') as fd:
            fd.write('[DEFAULT]\ntest=true\n\n')
        self.assertTrue(cfg.load())
        self.assertEqual(cfg['test'], 'true')

    def test_reset(self):
        """Tests :meth:`smd.utils.Config.reset` function."""
        cfg = utils.Config(self.cfg_path)
        cfg['language'] = 'new lang'
        self.assertEqual(cfg['language'], 'new lang')
        cfg.reset()
        self.assertNotEqual(cfg['language'], 'new lang')

    def test_save(self):
        """Tests :meth:`smd.utils.Config.save` function."""
        cfg = utils.Config(self.cfg_path)
        self.assertFalse(os.path.exists(self.cfg_path))
        cfg.save()
        self.assertTrue(os.path.exists(self.cfg_path))


class TestManga(unittest.TestCase):

    """Tests :class:`smd.utils.Manga` class."""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.join(TEST_DIR, 'manga')
        cls.data_dir = os.path.join(DATA_DIR, 'manga')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)

    def test_init(self):
        """Tests :meth:`smd.utils.Manga.__init__` function."""
        path = os.path.join(self.test_dir, 'TestManga')
        title = 'Test Manga'
        url = 'http://test-manga.com'
        site = 'manga-site'
        manga = utils.Manga(path, title, url, site)
        self.assertEqual(manga.path, path)
        self.assertEqual(manga['title'], title)
        self.assertEqual(manga['url'], url)
        self.assertEqual(manga['site'], site)

    def test_str(self):
        """Tests :meth:`smd.utils.Manga.__str__` function."""
        title = 'test manga'
        manga = utils.Manga(self.test_dir, title=title)
        self.assertEqual(str(manga), title)

    def test_repr(self):
        """Tests :meth:`smd.utils.Manga.__repr__` function."""
        title = 'test manga'
        url = 'http://manga-test.com'
        site = 'test-site'
        manga = utils.Manga('path', title, url, site)
        exp_repr = '({}, {}, {})'.format(title, url, site)
        self.assertEqual(repr(manga), exp_repr)

    def test_from_folder(self):
        """Tests :meth:`smd.utils.Manga.from_folder` function."""
        manga_dir = os.path.join(self.data_dir, 'TestManga')
        manga = utils.Manga.from_folder(manga_dir)
        self.assertEqual(manga['title'], 'TestManga')
        self.assertEqual(manga['url'], 'mangas/testmanga.html')
        self.assertEqual(manga['site'], 'manga-test')

    def test_is_manga(self):
        """Tests :meth:`smd.utils.Manga.is_manga` function."""
        manga_dir = os.path.join(self.data_dir, 'TestManga')
        self.assertTrue(utils.Manga.is_manga(manga_dir))

    def test_save_data(self):
        """Tests :meth:`smd.utils.Manga.save_data` function."""
        utils.Manga(self.test_dir).save_data()
        self.assertTrue(os.path.isfile(utils.Manga._filename))


class TestFunctions(unittest.TestCase):

    """Tests functions on :mod:`smd.util`."""

    @classmethod
    def setUpClass(cls):
        cls.stdin = sys.stdin
        cls.sys_exit = sys.exit
        cls.test_dir = os.path.join(TEST_DIR, 'functions')
        cls.data_dir = DATA_DIR
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)

    @classmethod
    def tearDownClass(cls):
        sys.stdin = cls.stdin
        sys.exit = cls.sys_exit

    def tearDown(self):
        sys.stdin.close()
        sys.exit = self.sys_exit

    def test_create_config_folder(self):
        """Tests :func:`smd.util.create_config_folder` function."""
        exp_dir = os.path.join(os.path.expanduser('~'), 'smd')
        if os.path.exists(exp_dir):
            shutil.rmtree(exp_dir)
        config_dir = utils.create_config_folder()
        self.assertEqual(config_dir, exp_dir)
        self.assertTrue(os.path.isdir(exp_dir))

    def test_die(self):
        def _sys_exit(status=0):
            nonlocal works
            works = True
        works = False
        sys.exit = _sys_exit
        utils.die('testing die')
        self.assertTrue(works)

    def test_download(self):
        """Tests :func:`smd.util.download` function."""
        downloaders = [Downloader('d{}'.format(i)) for i in range(1, 4)]
        sys.stdin = StringIO("1\n1")
        manga = 'naruto'
        chap_selectors = None
        tryall = True
        success = utils.download(downloaders[:], manga, chap_selectors, tryall)
        self.assertFalse(success)

    def test_filter_downloaders(self):
        """Tests :func:`smd.util.filter_downloaders` function."""
        langs = 'en en es en ru'.split()
        downloaders = [Downloader('d{}'.format(i), lang)
                       for i, lang in enumerate(langs, 1)]
        sys.stdin = StringIO('1\n')
        downls = utils.filter_downloaders('wrong lang', downloaders)
        exp_downls = [d for d in downloaders
                      if d.lang == sorted(set(langs))[0]]
        self.assertEqual(downls, exp_downls)

    def test_get_mangas(self):
        """Tests :func:`smd.util.get_mangas` function."""
        mangas = utils.get_mangas(os.path.join(self.data_dir, 'mangas_folder'))
        self.assertEqual(len(mangas), 3)

    def test_get_text(self):
        """Tests :func:`smd.util.get_text` function."""
        tags = ['<p>h&eacute;llo\n<b>world</b>\n&ntilde;<i><!---c---></i></p>',
                '<p>\n\nhell&oacute;\n <a href="#">&lt;again&gt</a>\n\n\n</p>']
        exp_texts = ['héllo world ñ', 'helló  <again>']
        for tag, exp_text in zip(tags, exp_texts):
            with self.subTest(tag=tag):
                text = utils.get_text(BeautifulSoup(tag, 'html.parser'))
                self.assertEqual(text, exp_text)

    def test_list_downloaders(self):
        """Tests :func:`smd.util.list_downloaders` function."""
        langs = 'en es de'.split()
        downloaders = [Downloader('d{}'.format(i), lang)
                       for i, lang in enumerate(langs, 1)]
        utils.list_downloaders(downloaders)

    def test_mkdir(self):
        """Tests :func:`smd.util.mkdir` function."""
        sys.stdin = StringIO('td\ntd2\ntd3\n')
        test_dir = 'test_mkdir'
        dirs = [test_dir, test_dir, 'test\\/mkdir', 'test[>:-/]mkdir']
        for d in dirs:
            with self.subTest(d=d):
                utils.mkdir('.', d)
        self.assertTrue(os.path.isdir(test_dir))

    def test_resume(self):
        """Tests :func:`smd.util.resume` function."""
        i, j = 1, 2
        sys.stdin = StringIO('{} {}'.format(i, j))
        data_md = os.path.join(self.data_dir, 'mangas_folder')
        mangas_dir = os.path.join(self.test_dir, 'mangas_resume')
        shutil.copytree(data_md, mangas_dir)
        downloaders = [Downloader('util-test')]
        resumed_mangas = []
        downloaders[0].resume = lambda m: resumed_mangas.append(m['title'])
        utils.resume(downloaders, mangas_dir)
        exp_resumed_mangas = ['TestManga {}'.format(i),
                              'TestManga {}'.format(j)]
        self.assertEqual(resumed_mangas, exp_resumed_mangas)
        mangas_dirs = [os.path.join(mangas_dir, 'm{}'.format(i)),
                       os.path.join(mangas_dir, 'm{}'.format(j))]
        resumed_mangas = []
        utils.resume(downloaders, mangas_dirs)
        self.assertEqual(resumed_mangas, exp_resumed_mangas)

    @unittest.expectedFailure
    def test_fail_select_chapters(self):
        """Tests :func:`smd.util.select_chapters` function."""
        selectors = ['1:0', 'inject_code()', '1000']
        for selector in selectors:
            with self.subTest(selector=selector):
                utils.select_chapters([], selector)

    def test_select_chapters(self):
        """Tests :func:`smd.util.select_chapters` function."""
        with open(os.path.join(self.data_dir, 'chapters.json')) as data_fh:
            chapters = [tuple(l) for l in json.load(data_fh)]
        selectors = ['1:10', '-1', '!-3', '1,3,5', ':5, !3, 7:, !9:10']
        exp_values = [set(chapters[0:10]), set([chapters[-1]]),
                      set(chapters) - set([chapters[-3]]),
                      set([chapters[0], chapters[2], chapters[4]]),
                      set(chapters[:5]+chapters[6:]) -
                      set([chapters[2]]+chapters[8:10])]
        for selector, exp in zip(selectors, exp_values):
            with self.subTest(selector=selector):
                selec = utils.select_chapters(chapters, selector)
                self.assertEqual(selec, exp)

    def test_select_downloader(self):
        """Tests :func:`smd.util.select_downloader` function."""
        downloaders = [Downloader('d{}'.format(i)) for i in range(1, 4)]
        i = 2
        exp_downl = downloaders[i-1]
        sys.stdin = StringIO("{}\n{}\n{}".format(len(downloaders)+1, -1, i))
        downl = utils.select_downloader(downloaders)
        self.assertIs(downl, exp_downl)

    def test_select_lang(self):
        """Tests :func:`smd.util.select_lang` function."""
        langs = 'es en de'.split()
        i = 1
        stdin = "{}\n{}\n{}".format(len(langs)+1, -1, i)
        sys.stdin = StringIO(stdin)
        lang = utils.select_lang(langs)
        self.assertEqual(lang, langs[i-1])

    def test_select_manga(self):
        """Tests :func:`smd.util.select_manga` function."""
        i = 1
        mangas = 'm1 m2 m3'.split()
        sys.stdin = StringIO("{}\n{}\n{}".format(len(mangas)+1, -1, i))
        manga = utils.select_manga(mangas)
        exp_manga = mangas[i-1]
        self.assertEqual(manga, exp_manga)
        sys.stdin = StringIO("{},{}".format(len(mangas), i))
        exp_manga = [mangas[i-1], mangas[-1]]
        manga = utils.select_manga(mangas, multiple=True)
        self.assertEqual(manga, exp_manga)

    def test_set_site(self):
        """Tests :func:`smd.util.set_site` function."""
        downloaders = [Downloader('d{}'.format(i)) for i in range(1, 4)]
        i = 2
        site = 'd{}'.format(i)
        exp_downl = downloaders[i-1]
        utils.set_site(site, downloaders)
        self.assertIs(downloaders[0], exp_downl)
        sys.stdin = StringIO("{}\n{}\n{}".format(len(downloaders)+1, -1, i))
        exp_downl = downloaders[i-1]
        utils.set_site('unknow site', downloaders)
        self.assertIs(downloaders[0], exp_downl)

    def test_update(self):
        """Tests :func:`smd.util.update` function."""
        def update(manga):
            nonlocal updated_mangas
            updated_mangas.append(manga['title'])
        i, j = 1, 2
        sys.stdin = StringIO('{} {}'.format(i, j))
        data_md = os.path.join(self.data_dir, 'mangas_folder')
        mangas_dir = os.path.join(self.test_dir, 'mangas_update')
        shutil.copytree(data_md, mangas_dir)
        downloaders = [Downloader('util-test')]
        updated_mangas = []
        downloaders[0].update = update
        utils.update(downloaders, mangas_dir)
        exp_updated_mangas = ['TestManga {}'.format(i),
                              'TestManga {}'.format(j)]
        self.assertEqual(updated_mangas, exp_updated_mangas)
        mangas_dirs = [os.path.join(mangas_dir, 'm{}'.format(i)),
                       os.path.join(mangas_dir, 'm{}'.format(j))]
        updated_mangas = []
        utils.update(downloaders, mangas_dirs)
        self.assertEqual(updated_mangas, exp_updated_mangas)

    @unittest.skip("no implemented yet")
    def test_language_change(self):
        raise Exception('no implemented')
