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
import datetime
import eventlet

eventlet.monkey_patch()

encodings = ['utf-8', 'latin-1', 'windows-1250', 'ascii']
regex = regex.get()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Crawler(object):
    # initializer for the crawler, given a start_url or a test_url
    def __init__(self, start_url=None, test_url=None):
        # error checking for the inputs
        if start_url is None and test_url is None:
            raise InvalidInputError('Either the start url or the test url must be an url')
        if start_url is not None and test_url is not None:
            raise InvalidInputError('Either the start url or the test url must be null')
        if start_url and not requester.validate_url(start_url):
            raise InvalidUrlError('The start url must be a url, the following input is not: %s' % start_url)
        if test_url and not requester.validate_url(test_url):
            raise InvalidUrlError('The test url must be a url, the following input is not: %s' % test_url)
        self.hashes = set() # set of hash codes for unzipped m3u files (reduce redundant parsing)
        self.internal_links = deque() # deque of internal links, links that will be crawled
        self.host_links = deque() # deque of host_links, links that host m3us
        self.host = None # the host url, the page at which the crawler begins crawler
        # Example: the start url of http://www.reddit.com/r/all is http://reddit.com
        self.visited = set() # set of internal links that have been visited
        self.test = False # boolean denoting whether this is a test run
        if test_url: # if a test_url is inputted
            self.host = um.prepare_netloc(test_url) # set the host to be the netloc of the test url
            self.streamer = Streamer('test') # set up a dummy streams collection in the database
            self.test = True
        if start_url: # if a start_url is inputted
            self.host = um.prepare_netloc(start_url) # prepare the host url (it should be the same as the start_url, but just in case)
            self.internal_links.append(self.host) # append the host to the internal links, begins crawling from that link
            now = datetime.datetime.now() # get the current time
            time = '%d-%d-%d' % (now.year, now.month, now.day)
            self.streamer = Streamer(time) # start a streamer based on that time
            self.visited.add(self.host) # add the host to visited
            while self.internal_links: # while there are internal links in the deque
                self.crawl(self.internal_links.popleft()) # crawl the link at the front of the deque
                while self.host_links: # if host links are found at the link
                    self.check_for_files(self.host_links.popleft()) # check for m3us, zip files, streams, etc. at the host links

    # crawls a page by extracting its text and referenced urls, adds internal urls found to the internal_links deque
    def crawl(self, page):
        if not requester.validate_url(page): # if the page is not an url
            raise InvalidUrlError('Cannot crawl page of invalid url: ' + str(page))
        request = requester.make_request(page) # make a request to the page
        if request: # if it's a valid request
            try:
                soup = BeautifulSoup(request.text, 'html.parser') # try making a bs4 soup from the request
            except NotImplementedError: # this error appears from time to time (not sure why ¯\_(ツ)_/¯)
                print('The following page caused an error in the soup %s' % str(page))
            else:
                if soup:
                    self.check_text_urls(soup, page) # check text urls
                    self.check_ref_urls(soup) # check ref urls

    # checks the referenced urls of a page, takes a bs4 soup as input
    def check_ref_urls(self, soup):
        for a in soup.find_all('a', href=True): # extracts all hrefs (referenced urls) from the page
            url = a.get('href') # get the link at the href
            if not re.search(regex['invalid'], url): # if the url is not invalid (empty url, javascript url, redirects with # to same page)
                url = urljoin(self.host, url) # join the url with the host (for partial urls)
                # example: urljoin(/r/all, http://reddit.com) -> http://reddit.com/r/all
                url = self.fix_url(url) # fixes the url by reducing queries, unnecessary slashes, identifiers and ports (reduce
                #  redundant requests to the same page) as well as expanding shortened non-internal urls
                if url and url not in self.visited: # if a url is returned and it has not been visited
                    self.visited.add(url) # add to visited
                    self.check_for_files(url) # check for m3us, zips, stream links etc. from the url
                    if requester.internal(url, self.host) and not re.search(regex['m3u'], url): # if it's internal
                        self.internal_links.append(url) # add it to the internal_links to be crawled (tail end recursion leads to
                        # stack over flow, thus an iterative approach is used

    # retrieves the text of a page using beautiful soup
    def check_text_urls(self, soup, parent):
        for br in soup.find_all('br'): # append line breaks to breaks (sometimes the br tag does not create a break in text, leading
            # to urls being lumped together
            br.append('\n')
        for div in soup.find_all('div'): # append line breaks to div tags for the same reason
            div.append('\n')
        if soup.text: # if text is found
            splitext = soup.text.splitlines() # split the text
            if splitext: # additional check just to be sure ?
                self.parse_text(splitext, parent) # parse the text

    # parse the text of both websites and m3u files to look for m3u files, zip files, and stream links
    def parse_text(self, splitext, parent):
        splitext = list(filter(lambda x: not re.match(regex['whitespace'], x), splitext)) # creates an array from the text and removes
        # empty whitespace from the array
        splitext_iter = iter(splitext) # creates an iterator of the splitext array
        internal_m3us = set() # set of internal m3us (network locations of m3us found on the page)
        ext_title = None
        if splitext_iter: # check if there is text
            try: # try loop to catch the end of iteration
                while True: # iterates over all lines in splitext using an iterator
                    curr = next(splitext_iter).strip()
                    ext_above = False
                    while re.search(regex['ext'], curr): # while an #EXT line is found, continue
                        ext_title = curr
                        curr = next(splitext_iter).strip()
                        ext_above = True # set ext_above to True
                    if ext_above and not requester.validate_url(curr): # if an #EXT line is above and the line is not a url, then it
                        # is properly a relative link, and a full link can be created by joining it to the parent
                        curr = urljoin(parent, curr)
                    url = self.fix_url(curr) # fix the format of the url
                    if url: # if a url is returned
                        netloc = um.prepare_netloc(url) # prepare netloc to check if the netloc is already in the internal m3us
                        # this prevents redundantly checking the same network location as sometimes dozens of m3us with only one stream
                        # from the same ip address are contained in an m3u, noted that internal m3us (m3us originating from the start site)
                        # are always parsed
                        if netloc not in internal_m3us:
                            if not ext_above or ext_above and re.search(regex['m3u'], url, re.IGNORECASE): # if it's an m3u in an m3u
                                # or a regular m3u not in a m3u
                                if url not in self.visited:
                                    self.visited.add(url)
                                    if not self.test:
                                        if re.search(regex['m3u'], parent, re.IGNORECASE): # if it's an m3u
                                            self.host_links.appendleft(url) # add it to the front of the deque (avoid stack overflow error)
                                        else:
                                            self.host_links.append(url) # append to the end of the deque
                                    else: # for testing purpose
                                        self.check_for_files(url)
                            elif ext_above and not re.search(regex['ignore'], url): # if ext_above and it is not an m3u then it is
                                # probably a stream link, certain stream links are ignored like audio files (have extensions like .mp3
                                # or .aac,) or streams originating from archive.org (give no information about the ip address as they
                                # are archives
                                self.streamer.add_to_streams(url, self.host, ext_title) # add  the stream to the database
                            if re.search(regex['m3u'], url) and not requester.internal(url, self.host): # if an m3u was found and it was
                                # not internal
                                internal_m3us.add(netloc)
            except StopIteration: # stop the iteration
                pass

    # checks for m3us, zip files, pastebin files and important html pages of a url
    def check_for_files(self, url):
        if not requester.validate_url(url): # validate the url
            raise InvalidUrlError('Cannot check_for_files for m3u files of the following url: %s' % str(url))
        parsed = urlparse(url) # parse the url into components
        url_search = parsed.path + parsed.query # search the path and query not the network location (reduces false flags)
        if re.search(regex['m3u'], url_search) or (re.search(regex['dl'], url_search) and not re.search(regex['ndl'], url_search)
        and (not requester.internal(url, self.host) or self.test)) or re.search(regex['zip'], url_search) or re.search(regex['raw'], url):
            # if important tags are found in the url_search or the url itself
            request = requester.make_request(url) # make a request to the url
            if request: # if the request is valid
                self.extract_file(request) # extract the request

    # extracts a url flagged as important based on its request
    def extract_file(self, request):
        file_type = requester.get_format(request) # get the file type of the request
        if file_type == 'm3u': # if it's a m3u
            splitext = request.text.splitlines()
            if splitext:
                self.parse_text(splitext, request.url)  # parse its text if the splitext is not empty
        elif file_type == 'zip': # if it's a zip file
            self.unzip(request) # unzip the zip file
        elif file_type == 'html' and not re.search(r'\.php', request.url): # if it's an html file and not a .php file
            self.crawl(request.url) # crawl the request's url

    # unzips a request flagged as a zip file
    def unzip(self, request):
        if request is None or not isinstance(request, Response):
            raise InvalidRequestError('Cannot unzip invalid make_request')
        try:
            z = zipfile.ZipFile(io.BytesIO(request.content)) # try creating a zipfile from the request's content
        except BadZipFile: # if it's unable to create a zipfile, pass
            pass
        else: # otherwise
            for info in z.infolist(): # for file in the zip file
                if re.search(regex['m3u'], info.filename): # if an m3u file extension is found in the file's name
                    f = z.read(info.filename) # read the zipfile
                    hash_num = requester.hash_content(f) # hash the content of the m3u
                    if hash_num not in self.hashes: # check if its hash code is in the hashes
                        self.hashes.add(hash_num) # if not add it to the hashes
                        for e in encodings: # attempt to decode the file by trying different encoding
                            try:
                                splitext = f.decode(e).splitlines() # create splitext from the decoded file
                            except UnicodeDecodeError: # if it's unable to decode it, pass
                                pass
                            else:
                                if splitext: # if a non-empty splitext is found
                                    self.parse_text(splitext, request.url) # parse the splitext
                                    break # break from the for loop

    # fixes a url to reduce redundant requests, as well as make checking for positive flags easier
    def fix_url(self, url):
        if not requester.validate_url(url):
            return None
        fixed_url = um.reduce_queries(um.phish(um.reduce(url))) # reduces queries redundant backslashes and fixes phishing of a url
        if not requester.internal(fixed_url, self.host): # if the url is not internal to the host
            fixed_url = um.expand(fixed_url) # expand the url if it's a shortened url
        if fixed_url in self.visited: # if the fixed_url is in self.visited
            return None # return None, as we do not want to do anything with the url
        return fixed_url

    def get_streamer(self):
        return self.streamer
