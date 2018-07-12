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
import eventlet

eventlet.monkey_patch()
regex = regex.get()


"""
Method: evaluate_stream
Purpose: determines whether or not an inputted url is a valid streaming link by creating a request to the url and checking the content
Input:
    url: url whose stream status is being determined
Returns:
    True: if the format of the request is a stream
    False: otherwise
Raises:
    InvalidUrlError: if the url is not a valid url
    StreamTimedOutError: if the request to the stream times out
"""

def evaluate_stream(url):
    if not validate_url(url):
        raise InvalidUrlError('Cannot evaluate stream of invalid url: %s' % url)
    timeout = 5 #increasing the timeout will lead to more time being spent on checking potentially deprecated streams, leading
    # to a longer total runtime, however, it will also lead to a greater accuracy as there are some outlier links that do work
    # but simply take a while to load. I recommend keeping it around 5
    try:
        with eventlet.Timeout(timeout): #when requesting to a stream the request is unable to timeout, eventlet is used to spawn a
            # concurrent thread to whatever is in the with statement. The eventlet threads runs for a specified  amount of time
            # (in this case, whatever the value of timeout is). When the timer runs out, both threads terminate and an
            # eventlet.timeout.Timeout error is raised. By wrapping the with statement in a with loop and catching the Timeout error,
            # a timeout for the request is effectively created.
            try:
                r = requests.get(url, stream=True) # request to a stream
            except (ConnectionError, TooManyRedirects, ChunkedEncodingError): #non-timeout errors
                return False
    except eventlet.timeout.Timeout: #catch the timeout if it occurs
        raise StreamTimedOutError('%s timed out' % url) #raise the StreamTimedOutError, which will be handled differently than
    #the boolean
    if r: #if the request is valid
        if get_format(r) == 'stream': #if the content of the request is a stream
            return True #return True, found as stream
    return False

"""
Method: phrases
Purpose: extracts all phrases from the path and queries of an url as an array
Example:
    'http://www.reddit.com/r/all' -> ['r', 'all']
Inputs:
    url: the url whose phrases are extracted
Returns:
    an array of phrases
Raises:
    InvalidUrlError: if the url is invalid
"""

def phrases(url):
    if not validate_url(url):
        raise InvalidUrlError('Cannot find words of invalid url')
    path = urlparse(url).path + urlparse(url).query #gets the path and query of the url
    path = path.replace('%20', ' ') #replaces %20 with spaces
    p = re.findall(regex['phrases'], path) #finds all fragments that are purely letters and numbers
    return list(filter(lambda x: not re.match(r'^\d+$', x), p)) #filters out pure numbers from phrases, returns result as a list

"""
Method: phrases
Purpose: returns the number of queries in an url
Example:
    'http://www.reddit.com/r/all' -> 0
    'http://www.reddit.com/?username=me&password=cat' -> 2
Inputs:
    url: the url whose queries are counted
Returns:
    integer: number of queries
Raises:
    InvalidUrlError: if the url is invalid
"""

def queries(url):
    if not validate_url(url):
        raise InvalidUrlError('Cannot find params of invalid url')
    q = urlparse(url).query
    if q == '': #if the query is empty
        return 0
    return q.count('&') + 1 #plus one as the first query does not have an &

"""
Method: purity
Purpose: used to determine what percent of the paths of an url are purely letters and number (contain no metacharacters)
Example:
    http://reddit.com/r/all -> 100
    http://reddit.com/r/all/fat%20cat -> 66.6666
Inputs:
    url: the url whose purity is being determined
Returns:
    a float; the purity of the url
Raises:
    InvalidUrlError: if the url is not valid
"""

def purity(url):
    if not validate_url(url):
        raise InvalidUrlError('Cannot determine purity of invalid url: %s' % url)
    s = subpaths(url)
    total = len(s)
    if total == 0:
        return -1
    pure = 0
    for subpath in s:
        if re.search(regex['pure'], subpath):
            pure += 1
    return (pure/total) * 100

"""
Method: subpaths
Purpose: extracts the subpaths of a url
Example:
    https://stackoverflow.com/questions/1155617/count -> ['questions', '1155617', 'count'
Input:
    url: the url whose subpaths are being extracted
Returns:
    an array; strings
Raises:
    InvalidUrlError: if the inputted url is not valid
"""

def subpaths(url):
    if not validate_url(url):
        raise InvalidUrlError('Cannot find subpaths of invalid url: ' + str(url))
    path = urlparse(url).path
    if re.search(r'\/$', path): #deletes a / if it exists at the end of the path
        l = list(path)
        del l[-1]
        path = ''.join(l)
    if re.search(r'^\/', path): #deletes a / if its exists at the start of the path
        l = list(path)
        del l[0]
        path = ''.join(l)
    if path == '': #if the path is empty returns an empty array
        return []
    return path.split('/') #splits at backslashes

"""
Method: hash_content
Purpose: reads the content of a file and hashes it based off its content 
Inputs:
    content: the content of the file to be hashed
Returns:
    hexdigest: a hash code based on the content
Raises:
    InvalidInputError: if the content is none of not an instance of bytes 
"""
def hash_content(content):
    if content is None or not isinstance(content, bytes):
        raise InvalidInputError('Can only hash bytes, not ' + str(type(content)))
    h = hashlib.new('ripemd160')
    try:
        h.update(content)
    except TypeError:
        pass
    else:
        return h.hexdigest()

"""
Method: get_format
Purpose: reads a requests and returns the content
Example:
    http://reddit.com/r/all -> html
    http://192.68.12.4/channels -> m3u
    http://mediafire.com/test.zip -> zip
Input:
    r: a request
Returns:
    string: the format of the file
Raises:
    InvalidInputError: if r is none or not an html Response
"""

def get_format(r):
    if r is None or not isinstance(r, Response):
        raise InvalidInputError('Cannot find format of invalid make_request')
    try:
        f = r.headers['content-type'] #gets the content type
    except KeyError:
        pass
    else:
        if re.search(regex['m3u_fmt'], f, re.IGNORECASE): #if it matches the content headings of an m3u
            return 'm3u'
        if re.search(regex['zip_fmt'], f, re.IGNORECASE): #if it matches the content headings of a zip
            return 'zip'
        if re.search(regex['html_fmt'], f, re.IGNORECASE): #if it matches the content headings of an html
            return 'html'
        if re.search(regex['stream_fmt'], f, re.IGNORECASE): #if it matches the content headings of a stream
            return 'stream'

"""
Method: make_request
Purpose: makes a request to a url and pulls down its html content
Input:
    url: the url that a request is being made to
Returns:
    r: an html Response 
"""

def make_request(url):
    if not validate_url(url):
        raise InvalidUrlError('Cannot make a make_request to an invalid url: ' + str(url))
    session = requests.Session() #creates a requests session
    headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:32.0) Gecko/20100101 Firefox/32.0'} #spoofed browser heading
    retry = Retry(connect=1, backoff_factor=1) #sets retry and back off factor as to not overwhelm sites and prevent 429 status codes
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter) #I don't remember what these do
    session.mount('https://', adapter)
    try:
        r = requests.get(url, timeout=3, headers=headers) #make a request
    except (ConnectionError, ReadTimeout, TooManyRedirects, ChunkedEncodingError): #except connection errors
        pass
    else: #otherwise
        if r.status_code in [525, 526]: #these status codes are related to the cloudflare preventative bot net software
            scraper = cfscrape.create_scraper() #creates a scraper that can bypass cloudflare
            r = scraper.get(url) # makes a request through that scraper
        if r.ok or re.search(regex['streams'], r.url, re.IGNORECASE): #if the status code of the request is valid
            return r #returns the request

"""
Method: internal
Purpose: determines whether a url is internal to a host
Example:
    http://reddit.com/r/all is internal to http://reddit.com and is not internal to http://facebook.com
Inputs:
    url: the url whose internal status is defined
    host: the url whose network location is used to determine the internal status
Returns:
    True: if the url is internal
    False: otherwise
Raises:
    InvalidUrlError: if the url or host is invalid
"""

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

"""
Method: remove_identifier
Purpose: removes the identifiers from an url
Example:
    http://www.reddit.com -> http://reddit.com
Input:
    url: the url whose identifier is removed
Returns:
    url: the url with the identifier removed
Raises:
    InvalidUrlError: if the url is invalid
"""

def remove_identifier(url):
    if not validate_url(url):
        raise InvalidUrlError('Cannot remove the identifier of an invalid url: %s' % url)
    search = re.search(regex['identity'], url)
    if search:
        return search.group(1) + search.group(3) #search group 2 contains the identifier
    return url

"""
Method: validate_url
Purpose: checks whether an inputted string is an url, note that urls without schemes are considered invalid
Example:
    http://reddit.com -> True
    http://www.reddit.com/r/all -> True
    //www.reddit.com -> True
    www.reddit.com -> False
    [] -> False
    0 -> False
Input:
    url: object whose url status is being determined
Returns:
    True: if the url is a valid url
    False: otherwise
"""

def validate_url(url):
    if url is not None and isinstance(url, str) and validators.url(url):
        return True
    return False