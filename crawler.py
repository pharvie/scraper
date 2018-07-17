from database import *
import regex
from collections import deque
import urllib3
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from requests.models import Response
import zipfile
from zipfile import BadZipFile
import io
import re
from urllib.parse import urlparse
from pympler import asizeof
import datetime

encodings = ['utf-8', 'latin-1', 'windows-1250', 'ascii']
regex = regex.get()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Crawler(object):
    def __init__(self, start=None, override_start_url_check=False, overridden_host=None, test=None, limit=float('inf'), train=False):
        self.hashes = set()
        self.counter = 1
        self.limit = limit
        self.internal_links = deque()
        self.host_links = deque()
        self.train = train
        self.host = None
        self.visited = set()
        if test:
            self.host = um.prepare_netloc(test)
            self.visited.add(test)
            self.streamer = Streamer('test')
        if start:
            start = um.remove_identifier(start)
            if overridden_host:
                self.host = um.prepare_netloc(overridden_host)
            else:
                self.host = um.prepare_netloc(start)
            if not override_start_url_check and self.host != start:
                raise InvalidStartUrlError('The start page is %s and the host is %s, note that if override_start_url_check is set to'
                                           'False then the start page and host must be identical. Currently override_start_url_check'
                                           'is set to %s' % (start, self.host, override_start_url_check))
            self.internal_links.append(start)
            now = datetime.datetime.now()
            time = '%d-%d-%d:%d' % (now.year, now.month, now.day, 0 if now.hour < 12 else 12)
            self.streamer = Streamer('%s_streams' % time)
            self.visited.add(self.host)
            while self.counter < self.limit and self.internal_links:
                self.crawl(self.internal_links.popleft())

    def crawl(self, page):
        if not requester.validate_url(page):
            raise InvalidUrlError('Cannot crawl page of invalid url: ' + str(page))
        request = requester.make_request(page)
        if request:
            print('Crawling %s' % page)
            if self.counter % 10 == 0:
                print('After crawling %s from %s links the total size is in bytes is currently %s, the queue has %s items '
                      'and is %s bytes large, visited size is %s' % (self.counter, self.host, asizeof.asizeof(self),
                                                                     len(self.internal_links), asizeof.asizeof(self.internal_links),
                                                                     asizeof.asizeof(self.visited)))
            self.counter += 1
            try:
                soup = BeautifulSoup(request.text, 'html.parser')
            except NotImplementedError:
                print('The following page caused an error in the soup %s' % str(page))
            else:
                if soup:
                    self.check_text_urls(soup, page)
                    self.check_ref_urls(soup)

    def check_ref_urls(self, soup):
        for a in soup.find_all('a', href=True):
            url = a.get('href')
            if not re.search(regex['invalid'], url) and url != '':
                url = urljoin(self.host, url)
                url = self.fix_url(url)
                if url:
                    if url not in self.visited:
                        self.visited.add(url)
                        self.check_for_files(url)
                        if requester.internal(url, self.host) and not re.search(regex['m3u'], url):
                            self.internal_links.append(url)

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
                        netloc = um.prepare_netloc(url)
                        if netloc not in internal_m3us:
                            if not ext_above or ext_above and re.search(regex['m3u'], url, re.IGNORECASE):
                                if url not in self.visited:
                                    self.check_for_files(url)
                                    self.visited.add(url)
                            elif ext_above:
                                self.streamer.add_to_streams(url, self.host)
                            if re.search(regex['m3u'], url) and not requester.internal(url, self.host):
                                internal_m3us.add(netloc)
                    curr = next(splitext_iter).strip()
            except StopIteration:
                pass

    def check_for_files(self, url):
        if not requester.validate_url(url):
            raise InvalidUrlError('Cannot check_for_files for m3u files of the following url: %s' % str(url))
        parsed = urlparse(url)
        url_search = parsed.path + parsed.query
        if re.search(regex['m3u'], url_search) or (re.search(regex['dl'], url_search) and not re.search(regex['ndl'], url_search)) \
                or re.search(regex['zip'], url_search) or re.search(regex['raw'], url):
            request = requester.make_request(url)
            if request:
                if request.url != url:
                    self.visited.add(request.url)
                self.extract_file(request)

    def extract_file(self, request):
        file_type = requester.get_format(request)
        if file_type == 'm3u':
            splitext = request.text.splitlines()
            if splitext:
                self.parse_text(splitext, parent=request.url)
        elif file_type == 'zip':
            self.unzip(request)
        elif file_type == 'html' and not re.search(r'\.php', request.url):
            if request.url not in self.visited:
                self.internal_links.appendleft(request.url)
                self.visited.add(request.url)

    def unzip(self, request):
        if request is None or not isinstance(request, Response):
            raise InvalidRequestError('Cannot unzip invalid make_request')
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
        fixed_url = um.reduce_queries(um.phish(url))
        if not requester.internal(fixed_url, self.host):
            fixed_url = um.expand(fixed_url)
        if fixed_url in self.visited:
            return None
        return fixed_url

    def get_streamer(self):
        return self.streamer
