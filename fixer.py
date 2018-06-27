from exceptions import InvalidURLException, InvalidHostException, InvalidInputException
import requester
from urllib.parse import urljoin
import re
import regex

regex = regex.get()

def reduce(url, host):
    if not requester.validate(url):
        raise InvalidURLException('Cannot reduce invalid url: ' + str(url))
    if not requester.validate(host):
        raise InvalidHostException('Cannot fix partiality with invalid host: ' + str(url))
    s = re.search(regex['end'], url)
    if s:
        url = s.group(1)
    if requester.internal(url, host):
        s = re.search(regex['params'], url)
        if s:
            return s.group(1)
    return url


def expand(url):
    if not requester.validate(url):
        raise InvalidURLException('Cannot fix shortness of invalid url: ' + str(url))
    if re.search(regex['short'], url):
        request = requester.request(url)
        if request is not None:
            #print('Expanded', url, 'to', request.url)
            url = request.url
    return url


def phish(url):
    if url is None or not isinstance(url, str):
        raise InvalidInputException('Cannot fix invalid url: ' + str(url))
    url = url.replace(';=', '=')
    url = url.replace(' ', '%20')
    return url


def partial(url, host):
    if url is None or not isinstance(url, str):
        raise InvalidInputException('Cannot fix partiality of invalid url: ' + str(url))
    if not requester.validate(host):
        raise InvalidHostException('Cannot fix partiality with invalid host: ' + str(url))
    return urljoin(host, url)




