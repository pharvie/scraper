from database import *
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
from urllib.parse import urlparse
from pympler import asizeof
import datetime

encodings = ['utf-8', 'latin-1', 'windows-1250', 'ascii']
regex = regex.get()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Crawler(object):
    def __init__(self, host=None, test=None, limit=float('inf'), train=False):
        self.hashes = set()
        self.counter = 1
        self.limit = limit
        self.queue = Queue()
        self.train = train
        self.host = None
        self.visited = {}
        now = datetime.datetime.now()
        self.time = '%d-%d-%d:%d' % (now.year, now.month, now.day, 0 if now.hour < 12 else 12)
        self.streamer = Streamer('%s_streams' % self.time )
        if test:
            self.host = um.prepare(test)
            self.visited[test] = None
            self.streamer = Streamer('test')
        if host:
            self.host = um.prepare(host)
            self.queue.enqueue(self.host)
            self.visited[self.host] = None
            while self.counter < self.limit and not self.queue.empty():
                self.crawl(self.queue.dequeue())

    def crawl(self, page):
        if not requester.validate_url(page):
            raise InvalidUrlError('Cannot crawl page of invalid url: ' + str(page))
        request = requester.make_request(page)
        if request:
            print('Crawling %s: %s, total size is currently %s, the queue has %s items and is %s bytes large, visited size is %s' %
                  (page, self.counter, asizeof.asizeof(self), self.queue.size(), asizeof.asizeof(self.queue), asizeof.asizeof(self.visited)))
            self.counter += 1
            try:
                soup = BeautifulSoup(request.text, 'html.parser')
            except NotImplementedError:
                print('The following page caused an error in the soup %s' % str(page))
            else:
                if soup:
                    self.check_text_urls(soup, page)
                    self.check_ref_urls(soup, page)

    def check_ref_urls(self, soup, parent):
        for a in soup.find_all('a', href=True):
            url = a.get('href')
            if not re.search(regex['invalid'], url) and url != '':
                url = urljoin(self.host, url)
                url = self.fix_url(url)
                if url:
                    if url not in self.visited:
                        self.visited[url] = parent
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
                        netloc = um.prepare(url)
                        if netloc not in internal_m3us or requester.internal(url, self.host):
                            if not ext_above or ext_above and re.search(regex['m3u'], url, re.IGNORECASE):
                                if url not in self.visited:
                                    self.visited[url] = parent
                                    self.check_for_files(url)
                            elif ext_above:
                                self.streamer.add_to_stream(url, self.host)
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
                or re.search(regex['zip'], url_search) or re.search(regex['raw'], url_search):
            request = requester.make_request(url)
            if request:
                if request.url != url:
                    self.visited[request.url] = self.visited[url]
                self.extract_file(request)

    def extract_file(self, request):
        file_type = requester.get_format(request)
        if file_type == 'm3u':
            splitext = request.text.splitlines()
            if splitext:
                self.parse_text(splitext, parent=request.url)
        elif file_type == 'zip':
            self.unzip(request)
        elif file_type == 'html':
            self.crawl(request.url)

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
        fixed_url = (um.phish(url))
        if not requester.internal(fixed_url, self.host):
            fixed_url = um.expand(fixed_url)
        if fixed_url in self.visited:
            return None
        return fixed_url

    def get_streamer(self):
        return self.streamer

