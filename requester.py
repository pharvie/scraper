import validators
from exceptions import InvalidURLException, InvalidRequestException, InvalidInputException
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

def phrases(url):
    if not validate(url):
        raise InvalidURLException('Cannot find words of invalid url')
    path = urlparse(url).path
    phrases = re.findall(regex['phrases'], path)
    phrases = list(filter(lambda x: not re.match(r'^\d+$', x), phrases))
    return phrases

def params(url):
    if not validate(url):
        raise InvalidURLException('Cannot find params of invalid url')
    parsed = urlparse(url)
    if parsed.query == '':
        return 0
    return 1


def purity(subpaths):
    if subpaths is None or not isinstance(subpaths, list):
        raise InvalidInputException('Cannot find purity of a non-list object')
    total = len(subpaths)
    if total == 0:
        return -1
    pure = 0
    for subpath in subpaths:
        if re.search(regex['pure'], subpath):
            pure += 1
    return (pure/total) * 100


def subpaths(url):
    if not validate(url):
        raise InvalidURLException('Cannot find subpaths of invalid url: ' + str(url))
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


def prepare(url):
    if not validate(url):
        raise InvalidURLException('Cannot prepare invalid url: ' + str(url))
    url = deport(url)
    parsed = urlparse(url)
    netloc = remove_identifier(parsed.netloc)
    return parsed.scheme + '://' + netloc


def remove_top(url):
    if not validate(url):
        raise InvalidURLException('Cannot remove top of invalid url: ' + str(url))
    url = deport(url)
    netloc = urlparse(url).netloc
    if re.search(regex['ip'], netloc):
        return netloc, 'ip'
    s = re.search(regex['top'], netloc)
    domain = remove_identifier(s.group(1))
    top = s.group(2)
    return domain, top


def deport(url):
    if not validate(url):
        raise InvalidURLException('Cannot remove port of invalid url: ' + str(url))
    search = re.search(regex['port'], url)
    if search:
        if search.group(3):
            return search.group(1) + search.group(3)
        return search.group(1)
    return url


def hash_content(content):
    if content is None or not isinstance(content, bytes):
        raise InvalidInputException('Can only hash bytes, not ' + str(type(content)))
    h = hashlib.new('ripemd160')
    try:
        h.update(content)
    except TypeError:
        print('An error occurred when hashing content')
    else:
        return h.hexdigest()

def get_format(r):
    if request is None or not isinstance(r, Response):
        raise InvalidRequestException('Cannot find format of invalid request')
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
    if not validate(url):
        raise InvalidURLException('Cannot make a request to an invalid url: ' + str(url))
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
    if not validate(url):
        raise InvalidURLException('Cannot define internal status of invalid url: ' + str(url))
    if not validate(host):
        raise InvalidURLException('Cannot define internal status with invalid base: ' + str(host))
    parsed_url = urlparse(url)
    parsed_base = urlparse(host)
    url_netloc = remove_identifier(parsed_url.netloc)
    base_netloc = remove_identifier(parsed_base.netloc)
    return url_netloc == base_netloc


def remove_identifier(netloc):
    if netloc is None or not isinstance(netloc, str):
        raise InvalidInputException('Cannot remove the identifier of an invalid network location: ' + str(netloc))
    search = re.search(regex['identity'], netloc)
    return search.group(2)


def host(url):
    if not validate(url):
        raise InvalidURLException('Cannot find host of invalid url: ' + str(url))
    parsed = urlparse(url)
    h = parsed.scheme + '://' + parsed.netloc
    return h


def validate(url):
    if url is not None and isinstance(url, str) and validators.url(url):
        return True
    return False
