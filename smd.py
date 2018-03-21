#!/usr/bin/env python3
'''
smd --- Simple Manga Downloader.
Copyright (c) 2017 Asiel Diaz Benitez.

smd is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

smd is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For more information see <http://www.gnu.org/licenses/>.
'''
import argparse
import http.cookiejar
from html.parser import HTMLParser
import json
import logging
import os
import re
import sys
from urllib.error import URLError, HTTPError
import urllib.request
import urllib.parse


class ParserDone(Exception):
    def __init__(self, res):
        Exception.__init__(self)
        self.res = res


class WarningFound(Exception):
    def __init__(self, url):
        Exception.__init__(self)
        self.url = url


class Downloader():
    def __init__(self):
        self.lang = ''
        self.id = ''
        self.url_opener = None

    def download(self):
        pass

    def __str__(self):
        return "%s (%s)" % (self.id, self.lang.upper())

    def mkchdir(self, path):
        if os.path.exists(path):
            if not os.path.isdir(path):
                print("[-] Error: can't create directory, file '%s' already exist."
                      % path)
                exit()
        else:
            os.mkdir(path)
        os.chdir(path)

    def gen_name(self, img_numb, img_count, img_name):
        zeros = len(str(img_count)) - len(str(img_numb))
        ext = img_name.split('.')
        if len(ext) < 2:
            ext = 'jpg'
        else:
            ext = ext.pop()
        out_file = '%s%i.%s' % ('0'*zeros, img_numb, ext)  # ex. 001.jpg
        return out_file

    def getJSON(self, url):
        try:
            while True:
                try:
                    with self.url_opener.open(url) as resp:
                        return json.loads(resp.read().decode(errors='ignore'))
                except ConnectionResetError as err:
                    logging.error("[%s] %s: %s", self.id, url, err)
                    continue
        except URLError as err:
            logging.error("[%s] %s: %s", self.id, url, err)
        return None

    def down_file(self, url, outFile):
        try:
            while True:
                try:
                    with self.url_opener.open(url) as resp, open(outFile, 'bw') as outf:
                        outf.write(resp.read())
                except ConnectionResetError as err:
                    logging.error("[%s] %s", self.id, err)
                    continue
                else:
                    break
        except URLError as err:
            logging.error("[%s] Downloading %s: %s", self.id, url, err)
            return False
        else:
            logging.info("[%s] Downloading %s...SUCCESS", self.id, url)
            return True

    def find(self, parser, url):
        try:
            while True:
                try:
                    with self.url_opener.open(url) as resp:
                        parser.feed(resp.read().decode(errors='ignore'))
                except ConnectionResetError as err:
                    logging.error("[%s] %s", self.id, err)
                except WarningFound as warn:
                    url = warn.url
                else:
                    break
        except HTTPError as httpErr:
            logging.error("[%s] %s: %s", self.id, httpErr, url)
        except URLError as urlErr:
            logging.error("[%s] %s: %s", self.id, urlErr.reason.strerror, url)
        except ParserDone as pd:
            return pd.res
        else:
            logging.error('[%s] Parser failed in: %s', self.id, url)
        return []


class TuMangaOnline(Downloader):
    def __init__(self):
        self.lang = 'es'
        self.site_url = 'https://www.tumangaonline.com'
        self.id = 'tumangaonline'
        cj = http.cookiejar.MozillaCookieJar()
        # cj.load('cookies.txt')
        self.url_opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cj))
        self.url_opener.addheaders = [
            ('Host', 'www.tumangaonline.com'),
            ('User-Agent', USER_AGENT),
            ('Accept', 'application/json, text/plain, */*'),
            ('Accept-Language', 'en-US,en;q=0.5'),
            ('X-Requested-With', 'XMLHttpRequest'),
            ('Cache-mode', 'no-cache'),
            ('Referer', 'https://www.tumangaonline.com'),
            ('DNT', '1'),
            ('Connection', 'keep-alive')
        ]

    def download(self, manga, startChapter):
        try:
            manga_dir = os.path.abspath(manga)
            downloads = 0
            url = '{}/api/v1/mangas?categorias=[]&defecto=1&generos=[]&itemsPerPage=20&nameSearch={}&page=1&puntuacion=0&searchBy=nombre&sortDir=asc&sortedBy=nombre'.format(self.site_url, urllib.parse.quote_plus(manga))
            print("[%s] Looking for '%s' ..." % (self.id, manga))
            resp = self.getJSON(url)
            if not resp:
                print('[-] Error: can\'t get server response.')
                return downloads
            print("Found:")
            for resp_manga in resp['data']:
                nombre = resp_manga['nombre']
                print("\t* '{}'".format(nombre))
                if nombre.lower() == manga.lower():
                    manga_id = resp_manga['id']
                    break
            if 'manga_id' not in dir():
                return downloads
            chapters = []
            next_url = '{}/api/v1/mangas/{}/capitulos?page=1&tomo=-1'.format(self.site_url,
                                                                             manga_id)
            while next_url:
                resp = self.getJSON(next_url)
                for chap in resp['data']:
                    chapters.append((chap['numCapitulo'], chap['subidas'][0]['idScan']))
                    next_url = resp['next_page_url']
                    chcount = len(chapters)
            if chcount > 0:
                print("[%s] Downloading '%s' (chapters: %i):"
                      % (self.id, manga, chcount))
                chapters.reverse()
            else:
                return downloads
            self.mkchdir(manga_dir)
            for chap, idscan in chapters[startChapter:]:
                chap_dir = os.path.join(manga_dir, chap)
                self.mkchdir(chap_dir)
                url = '{}/api/v1/imagenes?idManga={}&idScanlation={}&numeroCapitulo={}&visto=true'.format(self.site_url, manga_id, idscan, chap)
                resp = self.getJSON(url)
                images = json.loads(resp['imagenes'])
                img_count = len(images)
                for i, img_name in zip(range(1, img_count+1), images):
                    print("\r[%s] Downloading chapter:'%s' (image: %i/%i)"
                          % (self.id, chap, i, img_count), end='')
                    # GET image:
                    url = 'https://img1.tumangaonline.com/subidas/{}/{}/{}/{}'.format(manga_id, chap, idscan, img_name)
                    out_file = self.gen_name(i, img_count, img_name)
                    if self.down_file(url, out_file):
                        downloads += 1
                    else:
                        print("\n[%s] Fail to download %s"
                              % (self.id, url), end="")
                if img_count > 0:
                    print()
                try:
                    os.rmdir(chap_dir)
                except:
                    pass
        except KeyboardInterrupt as ki:
            raise ki
        except Exception as ex:
            exec_type, exc_obj, exc_tb = sys.exc_info()
            logging.error("[%s] in line %s: %s", self.id, exc_tb.tb_lineno, str(ex))
        finally:
            try:
                os.chdir(os.path.dirname(manga_dir))
                os.rmdir(manga_dir)
            except:
                pass
            return downloads


class NineManga(Downloader):
    class ChapterList(HTMLParser):
        def __init__(self, site_url):
            HTMLParser.__init__(self)
            self.inside_div = False
            self.inside_warn = False
            self.chapters = []
            self.site_url = site_url

        def handle_starttag(self, tag, attrs):
            if self.inside_div:
                if tag == 'a':
                    attrs = dict(attrs)
                    try:
                        if attrs['class'] == 'chapter_list_a':
                            self.chapters.append((attrs['href'],
                                                  attrs['title']))
                    except KeyError:
                        pass
            elif self.inside_warn:
                if tag == 'a':
                    self.__init__()
                    raise WarningFound(dict(attrs)['href'])
            elif tag == 'div':
                try:
                    cls = dict(attrs)['class']
                    if cls == 'silde':
                        self.inside_div = True
                    elif cls == 'warning':
                        self.inside_warn = True
                except KeyError:
                    pass

        def handle_endtag(self, tag):
            if self.inside_div and tag == 'div':
                raise ParserDone(self.chapters)

    class ImgPageList(HTMLParser):
        def __init__(self, site_url):
            HTMLParser.__init__(self)
            self.inside_select = False
            self.urls = []
            self.site_url = site_url

        def handle_starttag(self, tag, attrs):
            if self.inside_select:
                if tag == 'option':
                    self.urls.append(self.site_url + dict(attrs)['value'])
            elif tag == 'select':
                attrs = dict(attrs)
                try:
                    if attrs['id'] == 'page':
                        self.inside_select = True
                except KeyError:
                    pass

        def handle_endtag(self, tag):
            if self.inside_select and tag == 'select':
                raise ParserDone(self.urls)

    class ImgUrl(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag == 'img':
                attrs = dict(attrs)
                try:
                    if 'manga_pic' in attrs['class'].split():
                        raise ParserDone([attrs['src']])
                except KeyError:
                    pass

    def __init__(self, lang):
        self.lang = lang
        self.site_url = 'http://%s.ninemanga.com' % self.lang
        self.id = 'ninemanga-' + self.lang
        cj = http.cookiejar.MozillaCookieJar()
        self.url_opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cj))
        self.url_opener.addheaders = [
            ('Host', '%s.ninemanga.com' % self.lang),
            ('User-Agent', USER_AGENT),
            ('Referer', self.site_url),
            ('Accept', 'text/html,application/xhtml+xml,'
             'application/xml;q=0.9,*/*;q=0.8'),
            ('Accept-Language', 'en-US,en;q=0.5'),
            ('DNT', '1'),
            ('Connection', 'keep-alive'),
            ('Upgrade-Insecure-Requests', '1')
        ]

    def download(self, manga, start_chapter):
        try:
            manga_dir = os.path.abspath(manga)
            downloads = 0
            url = '%s/manga/%s.html' % (self.site_url, urllib.parse.quote(manga))
            print("[%s] Looking for '%s' ..." % (self.id, manga))
            chapters = self.find(self.ChapterList(self.site_url), url)
            chcount = len(chapters)
            if chcount > 0:
                print("[%s] Downloading '%s' (chapters: %i):"
                      % (self.id, manga, chcount))
                chapters.reverse()
            self.mkchdir(manga_dir)
            for (chapter, title) in chapters[start_chapter:]:
                chap_dir = os.path.join(manga_dir, title)
                self.mkchdir(chap_dir)
                img_pages = self.find(self.ImgPageList(self.site_url), chapter)
                img_count = len(img_pages)
                for i in range(1, img_count+1):
                    print("\r[%s] Downloading '%s' (image: %i/%i)"
                          % (self.id, title, i, img_count), end='')
                    for img_url in self.find(self.ImgUrl(), img_pages[i-1]):
                        out_file = self.gen_name(i, img_count, img_url)
                        if self.down_file(img_url, out_file):
                            downloads += 1
                        else:
                            print("\n[%s] Fail to download %s"
                                  % (self.id, img_url), end="")
                if img_count > 0:
                    print()
                try:
                    os.rmdir(chap_dir)
                except:
                    pass
        except KeyboardInterrupt as ki:
            raise ki
        except Exception as ex:
            exec_type, exc_obj, exc_tb = sys.exc_info()
            logging.error("[%s] in line %s: %s",
                          self.id, exc_tb.tb_lineno, str(ex))
        finally:
            try:
                os.chdir(os.path.dirname(manga_dir))
                os.rmdir(manga_dir)
            except:
                pass
            return downloads


class HeavenManga(Downloader):
    class ChapterList(HTMLParser):
        def __init__(self):
            HTMLParser.__init__(self)
            self.inside_ul = False
            self.chapters = []

        def handle_starttag(self, tag, attrs):
            if self.inside_ul:
                if tag == 'a':
                    attrs = dict(attrs)
                    self.chapters.append((attrs['href'], attrs['title']))
            elif tag == 'ul':
                try:
                    if dict(attrs)['id'] == 'holder':
                        self.inside_ul = True
                except KeyError:
                    pass

        def handle_endtag(self, tag):
            if self.inside_ul and tag == 'ul':
                raise ParserDone(self.chapters)

    class ChapterUrl(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag == 'a':
                attrs = dict(attrs)
                try:
                    if attrs['id'] == 'l':
                        raise ParserDone([attrs['href']])
                except KeyError:
                    pass

    class ImgPageList(HTMLParser):
        def __init__(self):
            HTMLParser.__init__(self)
            self.inside_select = False
            self.urls = []

        def handle_starttag(self, tag, attrs):
            if self.inside_select:
                if tag == 'option':
                    self.urls.append(dict(attrs)['value'])
            elif tag == 'select':
                self.inside_select = True

        def handle_endtag(self, tag):
            if self.inside_select and tag == 'select':
                raise ParserDone(self.urls)

    class ImgUrl(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag == 'img':
                attrs = dict(attrs)
                try:
                    if attrs['id'] == 'p':
                        raise ParserDone([attrs['src']])
                except KeyError:
                    pass

    def __init__(self):
        self.lang = 'es'
        self.site_url = 'http://heavenmanga.com'
        self.id = 'heavenmanga'
        cj = http.cookiejar.MozillaCookieJar()
        self.url_opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cj))
        self.url_opener.addheaders = [('User-Agent', USER_AGENT),
                                      ('Connection', 'keep-alive')]


    def download(self, manga, start_chapter):
        try:
            manga_dir = os.path.abspath(manga)
            manga = manga.replace(' ', '-').lower()
            downloads = 0
            url = '{0}/mangas/{1}/?manga_url={1}'.format(self.site_url, urllib.parse.quote(manga))
            print("[%s] Looking for '%s' ..." % (self.id, manga))
            chapters = self.find(self.ChapterList(), url)
            chcount = len(chapters)
            if chcount > 0:
                print("[%s] Downloading '%s' (chapters: %i):"
                      % (self.id, manga_dir, chcount))
                chapters.reverse()
            self.mkchdir(manga_dir)
            for (chapter, title) in chapters[start_chapter:]:
                self.mkchdir(title)
                for url in self.find(self.ChapterUrl(), chapter):
                    img_pages = self.find(self.ImgPageList(), url)
                    img_count = len(img_pages)
                    for i in range(1, img_count+1):
                        print("\r[%s] Downloading '%s' (image: %i/%i)"
                              % (self.id, title, i, img_count), end="")
                        for img_url in self.find(self.ImgUrl(), img_pages[i-1]):
                            out_file = self.gen_name(i, img_count, img_url)
                            if self.down_file(img_url, out_file):
                                downloads += 1
                            else:
                                print("\n[%s] Fail to download %s"
                                      % (self.id, img_url), end="")
                if img_count > 0:
                    print()
                try:
                    os.rmdir(title)
                except:
                    pass
        except KeyboardInterrupt as ki:
            raise ki
        except Exception as ex:
            exec_type, exc_obj, exc_tb = sys.exc_info()
            logging.error("[%s] in line %s: %s", self.id, exc_tb.tb_lineno, str(ex))
        finally:
            try:
                os.chdir(os.path.dirname(manga_dir))
                os.rmdir(manga_dir)
            except:
                pass
            return downloads


class MangaReader(Downloader):
    class ChapterList(HTMLParser):
        def __init__(self, site_url):
            HTMLParser.__init__(self)
            self.inside_table = False
            self.url = ''
            self.title = ''
            self.chapters = []
            self.site_url = site_url

        def handle_starttag(self, tag, attrs):
            if self.inside_table:
                if tag == 'a':
                    self.url = self.site_url + dict(attrs)['href']
            elif tag == 'table':
                try:
                    if dict(attrs)['id'] == 'listing':
                        self.inside_table = True
                except KeyError:
                    pass

        def handle_data(self, data):
            if self.url:
                self.title += data

        def handle_endtag(self, tag):
            if self.inside_table:
                if tag == 'a':
                    self.chapters.append((self.url,
                                          self.title.replace('\n', '')))
                    self.url = ''
                    self.title = ''
                elif tag == 'table':
                    raise ParserDone(self.chapters)

    class ImgPageList(HTMLParser):
        def __init__(self, site_url):
            HTMLParser.__init__(self)
            self.inside_select = False
            self.urls = []
            self.site_url = site_url

        def handle_starttag(self, tag, attrs):
            if self.inside_select:
                if tag == 'option':
                    self.urls.append(self.site_url + dict(attrs)['value'])
            elif tag == 'select':
                try:
                    if dict(attrs)['id'] == 'pageMenu':
                        self.inside_select = True
                except KeyError:
                    pass

        def handle_endtag(self, tag):
            if self.inside_select and tag == 'select':
                raise ParserDone(self.urls)

    class ImgUrl(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag == 'img':
                attrs = dict(attrs)
                try:
                    if attrs['id'] == 'img':
                        raise ParserDone([attrs['src']])
                except KeyError:
                    pass

    def __init__(self):
        self.lang = 'en'
        self.site_url = 'http://www.mangareader.net'
        self.id = 'mangareader'
        cj = http.cookiejar.MozillaCookieJar()
        self.url_opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cj))
        self.url_opener.addheaders = [('User-Agent', USER_AGENT),
                                 ('Connection', 'keep-alive')]

    def download(self, manga, start_chapter):
        try:
            manga_dir = os.path.abspath(manga)
            manga = manga.replace(' ', '-').lower()
            downloads = 0
            url = '%s/%s' % (self.site_url, urllib.parse.quote(manga))
            print("[%s] Looking for '%s' ..." % (self.id, manga))
            chapters = self.find(self.ChapterList(self.site_url), url)
            chcount = len(chapters)
            if chcount > 0:
                print("[%s] Downloading '%s' (chapters: %i):"
                      % (self.id, manga_dir, chcount))
            else:
                return downloads
            self.mkchdir(manga_dir)
            for (chapter, title) in chapters[start_chapter:]:
                chap_dir = os.path.join(manga_dir, title)
                self.mkchdir(chap_dir)
                img_pages = self.find(self.ImgPageList(self.site_url), chapter)
                img_count = len(img_pages)
                for i in range(1, img_count+1):
                    print("\r[%s] Downloading '%s' (image: %i/%i)"
                          % (self.id, title, i, img_count), end="")
                    for img_url in self.find(self.ImgUrl(), img_pages[i-1]):
                        out_file = self.gen_name(i, img_count, img_url)
                        if self.down_file(img_url, out_file):
                            downloads += 1
                        else:
                            print("\n[%s] Fail to download %s"
                                  % (self.id, img_url), end="")
                if img_count > 0:
                    print()
                try:
                    os.rmdir(chap_dir)
                except:
                    pass
        except KeyboardInterrupt as ki:
            raise ki
        except Exception as ex:
            exec_type, exc_obj, exc_tb = sys.exc_info()
            logging.error("[%s] in line %s: %s", self.id, exc_tb.tb_lineno, str(ex))
        finally:
            try:
                os.chdir(os.path.dirname(manga_dir))
                os.rmdir(manga_dir)
            except:
                pass
            return downloads


class MangaAll(Downloader):
    class ChapterList(HTMLParser):
        def __init__(self, site_url):
            HTMLParser.__init__(self)
            self.inside_section = False
            self.chapters = []
            self.site_url = site_url

        def handle_starttag(self, tag, attrs):
            if self.inside_section:
                if tag == 'a':
                    attrs = dict(attrs)
                    try:
                        self.chapters.append((attrs['href'], attrs['title']))
                    except KeyError:
                        pass
            elif tag == 'section':
                try:
                    if dict(attrs)['id'] == 'examples':
                        self.inside_section = True
                except KeyError:
                    pass

        def handle_endtag(self, tag):
            if self.inside_section and tag == 'section':
                raise ParserDone(self.chapters)

    class ImgPageList(HTMLParser):
        def __init__(self, chapter_url):
            HTMLParser.__init__(self)
            self.chapter_url = chapter_url
            self.regex = re.compile(r"var _page_total = '(?P<total>[0-9]+)';")
            self.inside_script = False
            self.total_pages = -1
            self.data = ""

        def handle_starttag(self, tag, attrs):
            if tag == 'script':
                self.inside_script = True

        def handle_data(self, data):
            if self.inside_script:
                self.data += data

        def handle_endtag(self, tag):
            if self.total_pages != -1:
                urls = [self.chapter_url+'?page='+str(n) for n in range(1, self.total_pages+1)]
                raise ParserDone(urls)
            elif tag == 'script':
                total = self.regex.findall(self.data)
                if len(total) != 0:
                    self.total_pages = int(total[-1])
                self.inside_script = False
                self.data = ""


    class ImgUrl(HTMLParser):
        def __init__(self):
            HTMLParser.__init__(self)
            self.inside_each = False
            self.img = ""

        def handle_starttag(self, tag, attrs):
            if self.inside_each:
                if tag == 'img':
                    self.img = dict(attrs)['src']
            elif tag == 'div':
                attrs = dict(attrs)
                try:
                    cls = attrs['class'].split()
                    if 'each-page' in attrs['class'].split():
                        self.inside_each = True
                except KeyError:
                    pass

        def handle_endtag(self, tag):
            if self.inside_each:
                raise ParserDone([self.img])

    def __init__(self):
        self.lang = 'en'
        self.site_url = 'http://mangaall.net'
        self.id = 'mangaall'
        cj = http.cookiejar.MozillaCookieJar()
        # cj.load('cookies.txt')
        self.url_opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cj))
        self.url_opener.addheaders = [
            ('Host', 'mangaall.net'),
            ('User-Agent', USER_AGENT),
            ('Referer', self.site_url),
            ('Accept', 'text/html,application/xhtml+xml,'
             'application/xml;q=0.9,*/*;q=0.8'),
            ('Accept-Language', 'en-US,en;q=0.5'),
            ('DNT', '1'),
            ('Connection', 'keep-alive'),
            ('Upgrade-Insecure-Requests', '1')
        ]

    def download(self, manga, start_chapter):
        try:
            manga_dir = os.path.abspath(manga)
            manga = manga.replace(' ', '-')
            downloads = 0
            url = '%s/manga/%s' % (self.site_url, urllib.parse.quote(manga))
            print("[%s] Looking for '%s' ..." % (self.id, manga))
            chapters = self.find(self.ChapterList(self.site_url), url)
            chcount = len(chapters)
            if chcount > 0:
                print("[%s] Downloading '%s' (chapters: %i):"
                      % (self.id, manga, chcount))
                chapters.reverse()
            self.mkchdir(manga_dir)
            for (chapter, title) in chapters[start_chapter:]:
                chap_dir = os.path.join(manga_dir, title)
                self.mkchdir(chap_dir)
                img_pages = self.find(self.ImgPageList(chapter), chapter)
                img_count = len(img_pages)
                for i in range(1, img_count+1):
                    print("\r[%s] Downloading '%s' (image: %i/%i)"
                          % (self.id, title, i, img_count), end='')
                    for img_url in self.find(self.ImgUrl(), img_pages[i-1]):
                        out_file = self.gen_name(i, img_count, img_url)
                        if self.down_file(img_url, out_file):
                            downloads += 1
                        else:
                            print("\n[%s] Fail to download %s"
                                  % (self.id, img_url), end="")
                if img_count > 0:
                    print()
                try:
                    os.rmdir(chap_dir)
                except:
                    pass
        except KeyboardInterrupt as ki:
            raise ki
        except Exception as ex:
            exec_type, exc_obj, exc_tb = sys.exc_info()
            logging.error("[%s] in line %s: %s", self.id, exc_tb.tb_lineno, str(ex))
        finally:
            try:
                os.chdir(os.path.dirname(manga_dir))
                os.rmdir(manga_dir)
            except:
                pass
            return downloads


def main(argv):
    class ListSites(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            print("Supported sites:")
            for downloader in DOWNLOADERS:
                print(" *", downloader)
            exit()
    p = argparse.ArgumentParser(description="Simple Manga Downloader",
                                epilog="Mail bug reports and suggestions to "
                                "<asieldbenitez@gmail.com>")
    p.add_argument("--version", action='version', version='%(prog)s 1.0')
    p.add_argument("-v", "--verbose",
                   help="show verbose messages",
                   action="store_true")
    p.add_argument("-l", "--list",
                   help="show a list of supported sites and exit",
                   nargs=0, action=ListSites)
    p.add_argument("--retry",
                   help="try to download manga from other sites if "
                   "the selected site have failed",
                   dest="retry", action="store_true")
    p.add_argument("-f", "--file",
                   help="use a file as input for mangas to download, the file "
                   "must have a list of manga names one by line",
                   nargs='?', type=argparse.FileType('r'), const=sys.stdin)
    p.add_argument("-s", "--site",
                   help="the site from which to download (default: %(default)s)",
                   metavar="SITE", choices=map(lambda d: d.id, DOWNLOADERS), default=DOWNLOADERS[0].id)
    p.add_argument("-c", "--chapter",
                   help="the chapter to start to download from",
                   type=int, default=1)
    p.add_argument("mangas",
                   help="the name of the manga to be downloaded",
                   metavar="MANGA", nargs="*")
    args = p.parse_args(argv)
    if args.verbose:
        logging.basicConfig(format='%(levelname)s:%(message)s',
                            level=logging.INFO)
    else:
        logging.basicConfig(filename='smd.log',
                            format='%(levelname)s:%(message)s',
                            level=logging.INFO)
    if args.file:
        args.mangas = []
        for manga in args.file.readlines():
            manga = manga.replace('\n', '').replace('-', ' ').split()
            manga = ' '.join([word.capitalize() for word in manga
                              if word and manga[0] != '#'])
            if manga:
                args.mangas.append(manga)
    if not args.mangas:
        p.print_usage()
    args.chapter -= 1  # lists index starts from 0
    for d in DOWNLOADERS:
        if d.id == args.site:
            downloader = d
    for manga in args.mangas:
        if downloader.download(manga, args.chapter):
            print()
        else:
            print("[%s] Failed to Download '%s'\n" % (args.site, manga))
            if args.retry:
                for d in DOWNLOADERS:
                    if d != downloader:
                        if d.download(manga, args.chapter):
                            break
                        else:
                            print("[%s] Failed to Download '%s'\n"
                                  % (downloader, manga))
        print()


USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; rv:52.0) Gecko/20100101 Firefox/52.0'
DOWNLOADERS = [TuMangaOnline(),
               NineManga('en'),
               NineManga('es'),
               NineManga('ru'),
               NineManga('de'),
               NineManga('it'),
               NineManga('br'),
               HeavenManga(),
               MangaReader(),
               MangaAll()]

if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print('[*] Operation canceled, Sayonara! :)')
