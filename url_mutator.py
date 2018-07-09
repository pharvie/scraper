from exceptions import *
import requester
from urllib.parse import urljoin
import re
import regex
from urllib.parse import urlparse

regex = regex.get()

def expand(url):
    if not requester.validate_url(url):
        raise InvalidUrlError('Cannot fix shortness of invalid url: ' + str(url))
    if re.search(regex['short'], url):
        request = requester.request(url)
        if request is not None:
            #print('Expanded', url, 'to', request.url)
            url = request.url
    return url


def phish(url):
    if url is None or not isinstance(url, str):
        raise InvalidInputError('Cannot fix invalid url: ' + str(url))
    url = url.replace(';=', '=')
    url = url.replace(' ', '%20')
    return url


def partial(url, host):
    if url is None or not isinstance(url, str):
        raise InvalidInputError('Cannot fix partiality of invalid url: ' + str(url))
    if not requester.validate_url(host):
        raise InvalidHostError('Cannot fix partiality with invalid host: ' + str(url))
    return urljoin(host, url)

def prepare(url):
    if not requester.validate_url(url):
        raise InvalidUrlError('Cannot prepare invalid url: ' + str(url))
    url = reduce(deport(requester.remove_identifier(url)))
    parsed = urlparse(url)
    return parsed.scheme + '://' + parsed.netloc

def remove_schema(url):
    if not requester.validate_url(url):
        raise InvalidUrlError('Cannot remove schema of invalid url: ' + str(url))
    parsed = urlparse(url)
    if parsed.query:
        return parsed.netloc + parsed.path + '?' + parsed.query
    return parsed.netloc + parsed.path

def remove_top(url):
    if not requester.validate_url(url):
        raise InvalidUrlError('Cannot remove top of invalid url: ' + str(url))
    url = deport(requester.remove_identifier(url))
    netloc = urlparse(url).netloc
    if re.search(regex['ip'], netloc):
        return netloc, 'ip'
    s = re.search(regex['top'], netloc)
    domain = s.group(1)
    top = s.group(2)
    return domain, top


def deport(url):
    if not requester.validate_url(url):
        raise InvalidUrlError('Cannot remove port of invalid url: ' + str(url))
    search = re.search(regex['port'], url)
    if search:
        if search.group(3):
            return search.group(1) + search.group(3)
        return search.group(1)
    return url


def reduce(url):
    if not requester.validate_url(url):
        raise InvalidUrlError('Cannot reduce invalid url: ' + str(url))
    s = re.search(regex['end'], url)
    if s:
        url = s.group(1)
    return url
