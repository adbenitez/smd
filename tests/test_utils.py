# -*- coding: utf-8 -*-
"""
.. module:: tests.test_utils

Offline tests for the :mod:`smd.util` module.

"""

import configparser
from io import StringIO
import json
import logging
import os
import shutil
import sys
import types
import typing
import unittest

from bs4 import BeautifulSoup  # type: ignore

import smd.utils

if typing.TYPE_CHECKING:
    from typing import TextIO


ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, 'data', 'util')
TEST_DIR = os.path.join(os.path.dirname(ROOT), 'test_utils_temp')


def setUpModule() -> None:
    os.mkdir(TEST_DIR)


def tearDownModule() -> None:
    shutil.rmtree(TEST_DIR)


class MetaFolder(smd.utils.MetaFolder):
    @staticmethod
    def from_folder(path: str):
        pass


class TestMetaFolder(unittest.TestCase):

    """Tests :class:`smd.utils.MetaFolder` class."""

    test_dir = None  # type: str
    mf_dir = None    # type: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_dir = os.path.join(TEST_DIR, 'metafolder')
        data_dir = os.path.join(DATA_DIR, 'metafolder')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)
        cls.mf_dir = os.path.join(data_dir, 'TestMetaFolder')

    def test_init(self) -> None:
        """Tests :meth:`smd.utils.MetaFolder.__init__` method."""
        self.assertEqual(MetaFolder.data_filename, 'data.json')
        path = 'testPath'
        mf = MetaFolder(path)
        self.assertEqual(mf.path, path)
        ignored = ['_ignored', 'path']
        self.assertEqual(mf._ignored, ignored)

    def test_load_from_folder(self) -> None:
        """Tests :meth:`smd.utils.MetaFolder._load_from_folder` method."""
        mf_dir = os.path.join(self.test_dir, 'test_load_from_folder')
        shutil.copytree(self.mf_dir, mf_dir)
        mf = MetaFolder(mf_dir)
        MetaFolder._load_from_folder(mf)
        self.assertEqual(mf.attr1, 1)  # type: ignore
        self.assertEqual(mf.attr2, 2)  # type: ignore

    def test_data_file_property(self) -> None:
        """Tests ``smd.utils.MetaFolder.data_file`` property."""
        path = 'testPath'
        mf = MetaFolder(path)
        exp_data_file = os.path.join(path, MetaFolder.data_filename)
        self.assertEqual(mf.data_file, exp_data_file)

    def test_is_valid(self) -> None:
        """Tests :meth:`smd.utils.MetaFolder.is_valid` method."""
        mf_dir = os.path.join(self.test_dir, 'test_is_valid')
        shutil.copytree(self.mf_dir, mf_dir)
        self.assertTrue(MetaFolder.is_valid(mf_dir))
        self.assertFalse(MetaFolder.is_valid(self.test_dir))

    def test_save_data(self) -> None:
        """Tests :meth:`smd.utils.MetaFolder.save_data` method."""
        mf_dir = os.path.join(self.test_dir, 'test_save_data')
        shutil.copytree(self.mf_dir, mf_dir)
        mf = MetaFolder(mf_dir)
        mf.attr1, mf.attr2, mf.attrNEW = 'a', 'b', 'c'  # type: ignore
        mf.save_data()
        with open(os.path.join(mf_dir, MetaFolder.data_filename)) as data_fh:
            data = json.load(data_fh)
        self.assertEqual(len(data), 3)
        self.assertEqual(mf.attr1, data['attr1'])  # type: ignore
        self.assertEqual(mf.attr2, data['attr2'])  # type: ignore
        self.assertEqual(mf.attrNEW, data['attrNEW'])  # type: ignore
        self.assertEqual('a', data['attr1'])  # type: ignore
        self.assertEqual('b', data['attr2'])  # type: ignore
        self.assertEqual('c', data['attrNEW'])  # type: ignore


class TestChapter(unittest.TestCase):

    """Tests :class:`smd.utils.Chapter` class."""

    test_dir = None  # type: str
    chap_dir = None  # type: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_dir = os.path.join(TEST_DIR, 'chapter')
        data_dir = os.path.join(DATA_DIR, 'chapter')
        cls.chap_dir = os.path.join(data_dir, 'chap1')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)

    def test_init(self) -> None:
        """Tests :meth:`smd.utils.Chapter.__init__` method."""
        self.assertEqual(smd.utils.Chapter.data_filename, 'chapter.json')
        path = 'test path'
        title = 'Test Chapter'
        url = 'http://test-chapter.com'
        chap = smd.utils.Chapter(path, title, url)
        self.assertEqual(chap.path, path)
        self.assertEqual(chap.title, title)
        self.assertEqual(chap.url, url)
        self.assertEqual(chap.current, -1)
        self.assertEqual(chap.images, [])

    def test_str(self) -> None:
        """Tests :meth:`smd.utils.Chapter.__str__` method."""
        title = 'test chapter'
        chap = smd.utils.Chapter('path', title, 'url')
        self.assertEqual(str(chap), title)

    def test_repr(self) -> None:
        """Tests :meth:`smd.utils.Chapter.__repr__` method."""
        title = 'test chapter'
        url = 'http://chapter-test.com'
        current = -1
        chap = smd.utils.Chapter('path', title, url)
        exp_repr = '({}, {}, {})'.format(title, url, current)
        self.assertEqual(repr(chap), exp_repr)

    def test_from_folder(self) -> None:
        """Tests :meth:`smd.utils.Chapter.from_folder` method."""
        chap_dir = os.path.join(self.test_dir, 'test_from_folder')
        shutil.copytree(self.chap_dir, chap_dir)
        chap = smd.utils.Chapter.from_folder(chap_dir)
        self.assertEqual(chap.title, 'chapter 1')
        self.assertEqual(chap.url, 'image_pages/naruto1_ch1_img1.html')
        self.assertEqual(chap.current, 3)
        self.assertEqual(len(chap.images), 3)


class TestConfig(unittest.TestCase):

    """Tests :class:`smd.utils.Config` class."""

    test_dir = None  # type: str
    cfg_path = None  # type: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_dir = os.path.join(TEST_DIR, 'config')
        cls.cfg_path = os.path.join(cls.test_dir, 'smd.cfg')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)

    def tearDown(self) -> None:
        if os.path.exists(self.cfg_path):
            os.remove(self.cfg_path)

    def test_init_getitem_and_setitem(self) -> None:
        """Tests :meth:`smd.utils.Config.__init__` and
        ``__getitem__``/``__setitem__`` methods."""
        cfg = smd.utils.Config(self.cfg_path)
        self.assertFalse(os.path.exists(self.cfg_path))
        self.assertEqual(cfg.path, self.cfg_path)
        self.assertIsInstance(cfg._parser, configparser.ConfigParser)
        cfg['test'] = 'true'
        self.assertEqual(cfg['test'], 'true')
        with self.assertRaises(KeyError):
            cfg['bad_key']

    def test_exists(self) -> None:
        """Tests :meth:`smd.utils.Config.exists` method."""
        cfg = smd.utils.Config(self.cfg_path)
        self.assertFalse(cfg.exists())
        with open(self.cfg_path, 'w') as fd:
            fd.write('[DEFAULT]\ntest=true\n\n')
        self.assertTrue(cfg.exists())

    def test_load(self) -> None:
        """Tests :meth:`smd.utils.Config.load` method."""
        cfg = smd.utils.Config(self.cfg_path)
        self.assertFalse(cfg.load())
        with self.assertRaises(KeyError):
            cfg['test']
        with open(self.cfg_path, 'w') as fd:
            fd.write('[DEFAULT]\ntest=true\n\n')
        self.assertTrue(cfg.load())
        self.assertEqual(cfg['test'], 'true')

    def test_reset(self) -> None:
        """Tests :meth:`smd.utils.Config.reset` method."""
        cfg = smd.utils.Config(self.cfg_path)
        cfg['language'] = 'new lang'
        self.assertEqual(cfg['language'], 'new lang')
        old_parser = cfg._parser
        cfg.reset()
        self.assertEqual(cfg['language'], 'SYSTEM')
        self.assertEqual(cfg['manga_dir'], '.')

    def test_save(self) -> None:
        """Tests :meth:`smd.utils.Config.save` method."""
        cfg = smd.utils.Config(self.cfg_path)
        self.assertFalse(os.path.exists(self.cfg_path))
        cfg.save()
        self.assertTrue(os.path.exists(self.cfg_path))


class TestConsoleFilter(unittest.TestCase):

    """Tests :class:`smd.utils.ConsoleFilter` class."""

    def test_filter(self) -> None:
        class DummyRecord(logging.LogRecord):
            def __init__(self):
                self.exc_info = 'info'
                self.exc_text = 'text'
        self.assertIsInstance(smd.utils.ConsoleFilter(), logging.Filter)
        record = DummyRecord()
        self.assertTrue(smd.utils.ConsoleFilter.filter(record))
        self.assertIsNone(record.exc_info)
        self.assertIsNone(record.exc_text)


class TestManga(unittest.TestCase):

    """Tests :class:`smd.utils.Manga` class."""

    test_dir = None  # type: str
    manga_dir = None  # type: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_dir = os.path.join(TEST_DIR, 'manga')
        data_dir = os.path.join(DATA_DIR, 'manga')
        cls.manga_dir = os.path.join(data_dir, 'TestManga')
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)

    def test_init(self) -> None:
        """Tests :meth:`smd.utils.Manga.__init__` method."""
        self.assertEqual(smd.utils.Manga.data_filename, 'manga.json')
        path = 'test path'
        title = 'Test Manga'
        url = 'http://test-manga.com'
        site = 'manga-site'
        manga = smd.utils.Manga(path, title, url, site)
        self.assertEqual(manga.path, path)
        self.assertEqual(manga.title, title)
        self.assertEqual(manga.url, url)
        self.assertEqual(manga.site, site)

    def test_str(self) -> None:
        """Tests :meth:`smd.utils.Manga.__str__` method."""
        title = 'test manga'
        manga = smd.utils.Manga('path', title, 'url', 'site')
        self.assertEqual(str(manga), title)

    def test_repr(self) -> None:
        """Tests :meth:`smd.utils.Manga.__repr__` method."""
        title = 'test manga'
        url = 'http://manga-test.com'
        site = 'test-site'
        manga = smd.utils.Manga('path', title, url, site)
        exp_repr = '({}, {}, {})'.format(title, url, site)
        self.assertEqual(repr(manga), exp_repr)

    def test_chapters(self) -> None:
        """Tests :meth:`smd.utils.Manga.chapters` method."""
        manga_dir = os.path.join(self.test_dir, 'test_chapters')
        shutil.copytree(self.manga_dir, manga_dir)
        manga = smd.utils.Manga.from_folder(manga_dir)
        chaps_gen = manga.chapters()
        self.assertIsInstance(chaps_gen, types.GeneratorType)
        chaps = list(chaps_gen)
        self.assertEqual(len(chaps), 5)
        for i, chap in enumerate(chaps, 1):
            with self.subTest(i=i):
                self.assertIsInstance(chap, smd.utils.Chapter)
                self.assertEqual(chap.title, 'chapter {}'.format(i))

    def test_from_folder(self) -> None:
        """Tests :meth:`smd.utils.Manga.from_folder` method."""
        manga_dir = os.path.join(self.test_dir, 'test_from_folder')
        shutil.copytree(self.manga_dir, manga_dir)
        manga = smd.utils.Manga.from_folder(manga_dir)
        self.assertEqual(manga.title, 'TestManga')
        self.assertEqual(manga.url, 'mangas/testmanga.html')
        self.assertEqual(manga.site, 'manga-test')

    def test_get_new_chapter_path(self) -> None:
        """Tests :meth:`smd.utils.Manga.get_new_chapter_path` method."""
        manga_dir = os.path.join(self.test_dir, 'test_get_new_chapter_path')
        os.mkdir(manga_dir)
        manga = smd.utils.Manga(manga_dir, 'title', 'url', 'site')
        self.assertEqual(manga.get_new_chapter_path(),
                         os.path.join(manga.path, '000001'))
        for i in range(1, 3):
            path = os.path.join(manga.path, str(i).zfill(6))
            with self.subTest(i=i):
                self.assertEqual(manga.get_new_chapter_path(), path)
            os.mkdir(path)
        self.assertEqual(manga.get_new_chapter_path(),
                         os.path.join(manga.path, '000003'))
        path = os.path.join(manga.path, '000002')
        os.rmdir(path)
        self.assertEqual(manga.get_new_chapter_path(), path)


class TestFunctions(unittest.TestCase):

    """Tests functions on :mod:`smd.util`."""

    stdin = None     # type: TextIO
    stdout = None    # type: TextIO
    test_dir = None  # type: str
    data_dir = None  # type: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.stdin = sys.stdin
        cls.stdout = sys.stdout
        cls.test_dir = os.path.join(TEST_DIR, 'functions')
        cls.data_dir = DATA_DIR
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)

    @classmethod
    def tearDownClass(cls) -> None:
        sys.stdin = cls.stdin
        sys.stdout = cls.stdout

    def tearDown(self) -> None:
        sys.stdin.close()
        sys.stdout = self.stdout

    def test_die(self) -> None:
        exp_msg = 'testing die'
        sys.stdout = StringIO()
        with self.assertRaises(SystemExit):  # type: ignore
            smd.utils.die(exp_msg)
        sys.stdout.seek(0)
        msg = sys.stdout.read()
        self.assertEqual(msg, exp_msg+'\n')

    def test_get_mangas(self) -> None:
        """Tests :func:`smd.util.get_mangas` function."""
        mangas_dir = os.path.join(self.test_dir, 'test_get_mangas')
        shutil.copytree(os.path.join(self.data_dir, 'mangas_folder'),
                        mangas_dir)
        mangas = smd.utils.get_mangas(mangas_dir)
        self.assertEqual(len(mangas), 3)
        for i, manga in enumerate(mangas, 1):
            with self.subTest(i=i):
                self.assertIsInstance(manga, smd.utils.Manga)
                self.assertEqual(manga.title, 'TestManga {}'.format(i))

    def test_get_text(self) -> None:
        """Tests :func:`smd.util.get_text` function."""
        tags = ['<p>h&eacute;llo\n<b>world</b>\n&ntilde;<i><!---c---></i></p>',
                '<p>\n\nhell&oacute;\n <a href="#">&lt;again&gt</a>\n\n\n</p>']
        exp_texts = ['héllo world ñ', 'helló  <again>']
        for tag, exp_text in zip(tags, exp_texts):
            with self.subTest(tag=tag):
                text = smd.utils.get_text(BeautifulSoup(tag, 'html.parser'))
                self.assertEqual(text, exp_text)

    def test_mkdir(self) -> None:
        """Tests :func:`smd.util.mkdir` function."""
        sys.stdin = StringIO('td\ntd2\ntd3\n')
        test_dir = 'test_mkdir'
        dirs = [test_dir, test_dir, 'test\\/mkdir', 'test[>:-/]mkdir']
        for d in dirs:
            with self.subTest(d=d):
                smd.utils.mkdir('.', d)
        self.assertTrue(os.path.isdir(test_dir))
        self.assertEqual(sys.stdin.read(), '')

    def test_persistent_operation(self) -> None:
        """Tests :func:`smd.util.persistent_operation` function."""
        @smd.utils.persistent_operation
        def testfunc():
            nonlocal msg, exec_times
            exec_times += 1
            if exec_times == 1:
                raise KeyboardInterrupt
            elif exec_times == 2:
                 msg = 'KeyboardInterrupt'
            elif exec_times == 3:
                raise SystemExit
            elif exec_times == 4:
                msg = 'SystemExit'
            else:
                raise Exception('Function called unexpectedly.')

        msg, exec_times = '', 0
        with self.assertRaises(KeyboardInterrupt):  # type: ignore
            testfunc()
        self.assertEqual(msg, 'KeyboardInterrupt')
        with self.assertRaises(SystemExit):  # type: ignore
            testfunc()
        self.assertEqual(msg, 'SystemExit')

    def test_select_chapters(self) -> None:
        """Tests :func:`smd.util.select_chapters` function."""
        with open(os.path.join(self.data_dir, 'chapters.json')) as data_fh:
            chapters = [smd.utils.Chapter('', title, url) for title, url
                        in json.load(data_fh)]
        selectors = ['1:10', '-1', '!-3', '1,3,5', ':5, !3, 7:, !9:10']
        exp_values = [chapters[:10], [chapters[-1]],
                      chapters[:-3] + chapters[-2:],
                      [chapters[0], chapters[2], chapters[4]],
                      chapters[:2]+chapters[3:5]+chapters[6:8]+chapters[10:]]
        for selector, exp in zip(selectors, exp_values):
            with self.subTest(selector=selector):
                selec = smd.utils.select_chapters(chapters, selector)
                self.assertEqual(selec, exp)
        selectors = ['1:0', 'inject_code()', '1000']
        for selector in selectors:
            with self.subTest(selector=selector):
                with self.assertRaises(SystemExit):  # type: ignore
                    smd.utils.select_chapters(chapters, selector)

    def test_select_mangas(self) -> None:
        """Tests :func:`smd.util.select_mangas` function."""
        i = 1
        mangas = [smd.utils.Manga('path', title, 'url', 'site')
                  for title in 'm1 m2 m3'.split()]
        sys.stdin = StringIO("{}\n{}\n{}".format(len(mangas)+1, -1, i))
        smangas = smd.utils.select_mangas(mangas, multiple=False)
        exp_mangas = [mangas[i-1]]
        self.assertEqual(smangas, exp_mangas)
        self.assertEqual(sys.stdin.read(), '')
        sys.stdin = StringIO("{},{}".format(len(mangas), i))
        exp_mangas = [mangas[-1], mangas[i-1]]
        smangas = smd.utils.select_mangas(mangas)
        self.assertEqual(smangas, exp_mangas)
        self.assertEqual(sys.stdin.read(), '')

