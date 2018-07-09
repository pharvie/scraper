from exceptions import *
import requester
import url_mutator as um
import regex
from my_queue import Queue
import urllib3
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from requests.models import Response
import zipfile
from zipfile import BadZipFile
import io
import re
import sys
from urllib.parse import urlparse
from database import Visitor
from pympler import asizeof

encodings = ['utf-8', 'latin-1', 'windows-1250', 'ascii']
regex = regex.get()
sys.setrecursionlimit(100000)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Crawler(object):
    def __init__(self, test=None, limit=float('inf'), train=False):
        self.hashes = set()
        self.streams = {}
        self.counter = 1
        self.limit = limit
        self.queue = Queue()
        self.train = train
        self.host = None
        self.visitor = None
        if test:
            self.host = requester.host(test)
            self.visitor = Visitor('test')

    def crawl(self, page, recurse=True):
        if not requester.validate_url(page):
            raise InvalidUrlError('Cannot crawl page of invalid url: ' + str(page))
        if self.host is None:
            self.host = requester.host(page)
            domain, top = um.remove_top(self.host)
            self.visitor = Visitor('%s_visited' % domain)
            self.visitor.visit_url(self.host, None)
            if page != self.host:
                raise InvalidInputError('The starting page must be the host of a webpage, the following page is not: %s' % page)
        request = requester.request(page)
        print('Crawling %s: %s, total size is currently %s, visitor size is %s, queue size is %s, streams size is %s' %
              (page, self.counter, asizeof.asizeof(self), asizeof.asizeof(self.visitor), asizeof.asizeof(self.queue),
               asizeof.asizeof(self.streams)))
        if request:
            self.counter += 1
            try:
                soup = BeautifulSoup(request.text, 'html.parser')
            except NotImplementedError:
                print('The following page caused an error in the soup %s' % str(page))
            else:
                if soup:
                    self.check_text_urls(soup, page)
                    self.check_ref_urls(soup, page)
                    while recurse and self.counter < self.limit and not self.queue.empty():
                        self.crawl(self.queue.dequeue())

    def check_ref_urls(self, soup, parent):
        if soup:
            for a in soup.find_all('a', href=True):
                url = a.get('href')
                if not re.search(regex['invalid'], url) and url != '':
                    url = urljoin(self.host, url)
                    url = self.fix_url(url)
                    if url:
                        """
                        print('Checked visited from ref')
                        self.visitor.visit_url(url, parent)
                        self.check_for_files(url)
                        """
                        try:
                            self.visitor.visit_url(url, parent)
                        except UrlPresentInDatabaseError:
                            pass
                        else:
                            self.check_for_files(url)
                            if requester.internal(url, self.host) and not re.search(regex['m3u'], url):
                                self.queue.enqueue(url)

    def check_text_urls(self, soup, parent):
        for br in soup.find_all('br'):
            br.append('\n')
        for div in soup.find_all('div'):
            div.append('\n')
        if soup.text:
            splitext = soup.text.splitlines()
            if splitext:
                self.parse_text(splitext, parent)

    def parse_text(self, splitext, parent):
        splitext = list(filter(lambda x: not re.match(regex['whitespace'], x), splitext))
        splitext_iter = iter(splitext)
        internal_m3us = set()
        if splitext_iter:
            curr = next(splitext_iter).strip()
            try:
                while True:
                    ext_above = False
                    while re.search(regex['ext'], curr):
                        curr = next(splitext_iter).strip()
                        ext_above = True
                    if ext_above and not requester.validate_url(curr):
                        curr = urljoin(parent, curr)
                    url = self.fix_url(curr)
                    if url:
                        url_netloc = um.prepare(url)
                        if url_netloc not in internal_m3us or requester.internal(url, self.host):
                            if not ext_above or ext_above and re.search(regex['m3u'], url, re.IGNORECASE) and \
                                    not re.search(regex['streams'], url, re.IGNORECASE):
                                try:
                                    self.visitor.visit_url(url, parent)
                                except UrlPresentInDatabaseError:
                                    pass
                                else:
                                    self.check_for_files(url)
                            else:
                                self.check_for_files(url)
                            if re.search(regex['m3u'], url) and not requester.internal(url, self.host):
                                internal_m3us.add(url_netloc)
                    curr = next(splitext_iter).strip()
            except StopIteration:
                pass

    def check_for_files(self, url):
        if not requester.validate_url(url):
            raise InvalidUrlError('Cannot check_for_files for m3u files of the following url: %s' % str(url))
        parsed = urlparse(url)
        url_search = parsed.path + parsed.query
        if re.search(regex['m3u'], url_search) or (re.search(regex['dl'], url_search) and not re.search(regex['ndl'], url_search)) \
                or re.search(regex['zip'], url_search) or re.search(regex['raw'], url_search):
            request = requester.request(url)
            if request:
                self.extract_file(request)
        elif re.search(regex['streams'], url_search):
            url_netloc = um.prepare(url)
            if url_netloc not in self.streams:
                self.streams[url_netloc] = set()
                self.streams[url_netloc].add(self.host)
                print(url_netloc, self.streams[url_netloc])

    def extract_file(self, request):
        file_type = requester.get_format(request)
        if file_type == 'm3u':
            splitext = request.text.splitlines()
            if splitext:
                self.parse_text(splitext, parent=request.url)
        elif file_type == 'zip':
            self.unzip(request)
        elif file_type == 'html':
            self.crawl(request.url, recurse=False)

    def unzip(self, request):
        if request is None or not isinstance(request, Response):
            raise InvalidRequestError('Cannot unzip invalid request')
        try:
            z = zipfile.ZipFile(io.BytesIO(request.content))
        except BadZipFile:
            pass
        else:
            for info in z.infolist():
                if re.search(regex['m3u'], info.filename):
                    f = z.read(info.filename)
                    hash_num = requester.hash_content(f)
                    if hash_num not in self.hashes:
                        self.hashes.add(hash_num)
                        for e in encodings:
                            try:
                                splitext = f.decode(e).splitlines()
                            except UnicodeDecodeError:
                                pass
                            else:
                                if splitext:
                                    self.parse_text(splitext, parent=request.url)
                                    break

    def fix_url(self, url):
        if not requester.validate_url(url):
            return None
        fixed_url = um.phish(url)
        if not requester.internal(fixed_url, self.host):
            fixed_url = um.expand(fixed_url)
        return fixed_url

    def get_streams(self):
        return self.streams

    def get_visitor(self):
        return self.visitor
