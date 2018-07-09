import validators
from exceptions import *
from urllib.parse import urlparse
import requests
from requests.models import Response
from requests.exceptions import ConnectionError, ReadTimeout, TooManyRedirects, ChunkedEncodingError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re
import cfscrape
import hashlib
import regex
#import vlc

regex = regex.get()
"""
def play_stream(url):
    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(url)
    media.get_mrl()
    player.set_media(media)
    player.play()
"""

def metacharacters(url):
    if not validate_url(url):
        raise InvalidUrlError('Cannot find metacharacters of invalid url')
    meta = set()
    for subpath in subpaths(url):
        for char in re.findall(regex['metacharacters'], subpath):
                meta.add(char)
    return meta

def phrases(url):
    if not validate_url(url):
        raise InvalidUrlError('Cannot find words of invalid url')
    path = urlparse(url).path + urlparse(url).query
    path = path.replace('%20', ' ')
    phrases = re.findall(regex['phrases'], path)
    phrases = list(filter(lambda x: not re.match(r'^\d+$', x), phrases))
    return phrases

def queries(url):
    if not validate_url(url):
        raise InvalidUrlError('Cannot find params of invalid url')
    parsed = urlparse(url)
    if parsed.query == '':
        return 0
    return 1

def purity(subpaths):
    if subpaths is None or not isinstance(subpaths, list):
        raise InvalidInputError('Cannot find purity of a non-list object')
    total = len(subpaths)
    if total == 0:
        return -1
    pure = 0
    for subpath in subpaths:
        if re.search(regex['pure'], subpath):
            pure += 1
    return (pure/total) * 100

def subpaths(url):
    if not validate_url(url):
        raise InvalidUrlError('Cannot find subpaths of invalid url: ' + str(url))
    path = urlparse(url).path
    if re.search(r'\/$', path):
        l = list(path)
        del l[-1]
        path = ''.join(l)
    if re.search(r'^\/', path):
        l = list(path)
        del l[0]
        path = ''.join(l)
    if path == '':
        return []
    subpaths = path.split('/')
    return subpaths

def hash_content(content):
    if content is None or not isinstance(content, bytes):
        raise InvalidInputError('Can only hash bytes, not ' + str(type(content)))
    h = hashlib.new('ripemd160')
    try:
        h.update(content)
    except TypeError:
        print('An error occurred when hashing content')
    else:
        return h.hexdigest()

def get_format(r):
    if request is None or not isinstance(r, Response):
        raise InvalidRequestError('Cannot find format of invalid request')
    try:
        f = r.headers['content-type']
    except KeyError:
        pass
    else:
        if re.search(regex['m3u_fmt'], f, re.IGNORECASE):
            return 'm3u'
        if re.search(regex['zip_fmt'], f, re.IGNORECASE):
            return 'zip'
        if re.search(regex['html_fmt'], f, re.IGNORECASE):
            return 'html'

def request(url):
    if not validate_url(url):
        raise InvalidUrlError('Cannot make a request to an invalid url: ' + str(url))
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    try:
        r = requests.get(url, timeout=5)
    except (ConnectionError, ReadTimeout, TooManyRedirects, ChunkedEncodingError):
        pass
    else:
        if r.status_code in [503, 525, 526]:
            #print('Cloudflare at', url)
            scraper = cfscrape.create_scraper()
            r = scraper.get(url)
        if r.ok or re.search(regex['streams'], r.url, re.IGNORECASE):
            return r

def internal(url, host):
    if not validate_url(url):
        raise InvalidUrlError('Cannot define internal status of invalid url: ' + str(url))
    if not validate_url(host):
        raise InvalidUrlError('Cannot define internal status with invalid base: ' + str(host))
    url = remove_identifier(url)
    host = remove_identifier(host)
    url_netloc = urlparse(url).netloc
    host_netloc = urlparse(host).netloc
    return url_netloc == host_netloc

def remove_identifier(url):
    if url is None or not validate_url(url):
        raise InvalidUrlError('Cannot remove the identifier of an invalid url: %s' % url)
    search = re.search(regex['identity'], url)
    if search:
        return search.group(1) + search.group(3)
    return url

def host(url):
    if not validate_url(url):
        raise InvalidUrlError('Cannot find host of invalid url: ' + str(url))
    parsed = urlparse(url)
    h = parsed.scheme + '://' + parsed.netloc
    return h

def validate_url(url):
    if url is not None and isinstance(url, str) and validators.url(url):
        return True
    return False
