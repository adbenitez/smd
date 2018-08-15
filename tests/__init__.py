# -*- coding: utf-8 -*-
'''
.. module:: tests

Tests for the ``smd`` application.

'''
import argparse
from io import StringIO
import logging
import os
import shutil
import sys
import typing
import unittest

import smd

if typing.TYPE_CHECKING:
    from typing import List, TextIO


def gettext(msg: str) -> str:
    return msg


ROOT = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.join(os.path.dirname(ROOT), 'test_smd_temp')
DATA_DIR = os.path.join(ROOT, 'data', 'smd')


def setUpModule() -> None:
    os.mkdir(TEST_DIR)
    smd._ = smd.downloader._ = smd.utils._ = gettext


def tearDownModule() -> None:
    shutil.rmtree(TEST_DIR)


class Downloader(smd.downloader.Downloader):

    """A dummy implementation of the abstract class
    :class:`smd.downloader.Downloader` for testing purposes"""

    def __init__(self, name: str = 'test-site', lang: str = 'en',
                 site_url: str = 'http://test-site.com') -> None:
        super().__init__(name, lang, site_url)
        self.logger = logging.getLogger()

    def _init_logger(self) -> None:
        pass

    def get_chapters(self, manga_url: str) -> list:
        return []

    def get_images(self, chap_url: str) -> list:
        return []

    def search(self, manga: str) -> list:
        return []


class TestFunctions(unittest.TestCase):

    """Tests functions on :mod:`smd`."""

    set_locale = smd.set_locale  # type: ignore
    CONF_DIR = smd.CONF_DIR  # type: str
    stdin = None     # type: TextIO
    # stdout = None    # type: TextIO
    test_dir = None  # type: str
    data_dir = None  # type: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.stdin = sys.stdin
        # cls.stdout = sys.stdout
        cls.test_dir = os.path.join(TEST_DIR, 'functions')
        cls.data_dir = DATA_DIR
        os.mkdir(cls.test_dir)
        os.chdir(cls.test_dir)

    @classmethod
    def tearDownClass(cls) -> None:
        smd.CONF_DIR = cls.CONF_DIR
        sys.stdin = cls.stdin
        # sys.stdout = cls.stdout

    def tearDown(self) -> None:
        smd.CONF_DIR = self.CONF_DIR
        smd.set_locale = TestFunctions.set_locale  # type: ignore
        sys.stdin.close()
        # sys.stdout = self.stdout

    def test_keyboard_interrupt(self) -> None:
        """Tests :func:`smd.keyboard_interrupt` decorator."""
        @smd.keyboard_interrupt
        def testfunc():
            raise KeyboardInterrupt
        exp_msg = '\n[*] Operation canceled, Sayonara! :)'
        sys.stdout = StringIO()
        with self.assertRaises(SystemExit):  # type: ignore
            testfunc()
        sys.stdout.seek(0)
        msg = sys.stdout.read()
        self.assertEqual(msg, exp_msg+'\n')

    def test_create_config_folder(self) -> None:
        """Tests :func:`smd.create_config_folder` function."""
        smd.CONF_DIR = os.path.join('nonexistent folder', 'test')
        with self.assertRaises(SystemExit):  # type: ignore
            smd.create_config_folder()
        exp_dir = os.path.join(self.test_dir, 'test_create_config_folder')
        smd.CONF_DIR = exp_dir
        with open(exp_dir, 'w') as d:
            pass
        with self.assertRaises(SystemExit):  # type: ignore
            smd.create_config_folder()
        os.remove(exp_dir)
        smd.create_config_folder()
        self.assertTrue(os.path.isdir(exp_dir))
        smd.create_config_folder()

    def test_download(self) -> None:
        """Tests :func:`smd.download` function."""
        downloaders = [
            Downloader('d{}'.format(i)) for i in range(1, 4)
        ]  # type: List[smd.downloader.Downloader]
        sys.stdin = StringIO("1\n1")
        manga = 'naruto'
        chap_selectors = ''
        tryall = True
        success = smd.download(downloaders[:], manga, chap_selectors, tryall)
        self.assertFalse(success)
        self.assertEqual(sys.stdin.read(), '')

    def test_filter_downloaders(self) -> None:
        """Tests :func:`smd.filter_downloaders` function."""
        langs = 'en en es en ru'.split()
        downloaders = [
            Downloader('d{}'.format(i), lang)
            for i, lang in enumerate(langs, 1)
        ]  # type: List[smd.downloader.Downloader]
        sys.stdin = StringIO('1\n')
        downls = smd.filter_downloaders('wrong lang', downloaders)
        exp_downls = [d for d in downloaders
                      if d.lang == sorted(set(langs))[0]]
        self.assertEqual(downls, exp_downls)
        self.assertEqual(sys.stdin.read(), '')

    def test_get_args_parser(self) -> None:
        """Tests :func:`smd.get_args_parser` function."""
        parser = smd.get_args_parser()  # type: argparse.ArgumentParser
        self.assertIsInstance(parser, argparse.ArgumentParser)

    def test_list_downloaders(self) -> None:
        """Tests :func:`smd.list_downloaders` function."""
        langs = 'en es de'.split()
        downloaders = [
            Downloader('d{}'.format(i), lang)
            for i, lang in enumerate(langs, 1)
        ]  # type: List[smd.downloader.Downloader]
        smd.list_downloaders(downloaders)

    def test_resume(self) -> None:
        """Tests :func:`smd.resume` function."""
        def resume(m: smd.utils.Manga):
            resumed_mangas.append(m.title)
        i, j = 1, 2
        sys.stdin = StringIO('{} {}'.format(i, j))
        data_md = os.path.join(self.data_dir, 'mangas_folder')
        mangas_dir = os.path.join(self.test_dir, 'mangas_resume')
        shutil.copytree(data_md, mangas_dir)
        downloaders = [
            Downloader('test-site')]  # type: List[smd.downloader.Downloader]
        resumed_mangas = []  # type: List[str]
        downloaders[0].resume = resume  # type: ignore
        smd.resume(downloaders, mangas_dir)
        exp_resumed_mangas = ['TestManga {}'.format(i),
                              'TestManga {}'.format(j)]
        self.assertEqual(resumed_mangas, exp_resumed_mangas)
        mangas_dirs = [os.path.join(mangas_dir, 'm{}'.format(i)),
                       os.path.join(mangas_dir, 'm{}'.format(j))]
        resumed_mangas = []
        smd.resume(downloaders, mangas_dirs)
        self.assertEqual(resumed_mangas, exp_resumed_mangas)
        self.assertEqual(sys.stdin.read(), '')

    def test_show_copyright(self) -> None:
        """Tests :func:`smd.show_copyright` function."""
        smd.show_copyright()

    def test_select_downloader(self) -> None:
        """Tests :func:`smd.select_downloader` function."""
        downloaders = [
            Downloader('d{}'.format(i)) for i in range(1, 4)
        ]  # type: List[smd.downloader.Downloader]
        i = 2
        exp_downl = downloaders[i-1]
        sys.stdin = StringIO("{}\n{}\n{}".format(len(downloaders)+1, -1, i))
        downl = smd.select_downloader(downloaders)
        self.assertIs(downl, exp_downl)
        self.assertEqual(sys.stdin.read(), '')

    def test_select_lang(self) -> None:
        """Tests :func:`smd.select_lang` function."""
        langs = 'es en de'.split()
        i = 1
        stdin = "{}\n{}\n{}".format(len(langs)+1, -1, i)
        sys.stdin = StringIO(stdin)
        lang = smd.select_lang(langs)
        self.assertEqual(lang, langs[i-1])
        self.assertEqual(sys.stdin.read(), '')

    def test_set_site(self) -> None:
        """Tests :func:`smd.set_site` function."""
        downloaders = [
            Downloader('d{}'.format(i)) for i in range(1, 4)
        ]  # type: List[smd.downloader.Downloader]
        i = 2
        site = 'd{}'.format(i)
        exp_downl = downloaders[i-1]
        smd.set_site(site, downloaders)
        self.assertIs(downloaders[0], exp_downl)
        sys.stdin = StringIO("{}\n{}\n{}".format(len(downloaders)+1, -1, i))
        exp_downl = downloaders[i-1]
        smd.set_site('unknow site', downloaders)
        self.assertIs(downloaders[0], exp_downl)
        self.assertEqual(sys.stdin.read(), '')

    def test_set_locale(self) -> None:
        """Tests :func:`smd.set_locale` function."""
        with self.assertRaises(NameError):
            _('test')  # type: ignore
        smd.set_locale('SYSTEM', '.')
        _('test')  # type: ignore
        smd.set_locale('unknow_Locale', '.')

    def test_update(self) -> None:
        """Tests :func:`smd.update` function."""
        def update(manga: smd.utils.Manga) -> None:
            nonlocal updated_mangas
            updated_mangas.append(manga.title)
        i, j = 1, 2
        sys.stdin = StringIO('{} {}'.format(i, j))
        data_md = os.path.join(self.data_dir, 'mangas_folder')
        mangas_dir = os.path.join(self.test_dir, 'mangas_update')
        shutil.copytree(data_md, mangas_dir)
        downloaders = [
            Downloader('test-site')]  # type: List[smd.downloader.Downloader]
        updated_mangas = []  # type: List[str]
        downloaders[0].update = update  # type: ignore
        smd.update(downloaders, mangas_dir)
        exp_updated_mangas = ['TestManga {}'.format(i),
                              'TestManga {}'.format(j)]
        self.assertEqual(updated_mangas, exp_updated_mangas)
        self.assertEqual(sys.stdin.read(), '')
        mangas_dirs = [os.path.join(mangas_dir, 'm{}'.format(i)),
                       os.path.join(mangas_dir, 'm{}'.format(j))]
        updated_mangas = []
        smd.update(downloaders, mangas_dirs)
        self.assertEqual(updated_mangas, exp_updated_mangas)

    def test_main(self) -> None:
        """Tests :func:`smd.main` function."""
        smd.set_locale = lambda lang, ldir: True  # type: ignore
        args_list = [['--license'], ['-h'], ['-v'], ['-l']]
        for args in args_list:
            with self.subTest(args=args):
                with self.assertRaises(SystemExit):  # type: ignore
                    smd.main(args)
