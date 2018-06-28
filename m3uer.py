import re
import requests
from requests.exceptions import ConnectionError, ReadTimeout, TooManyRedirects, ChunkedEncodingError

streams = []
regex = {
    'ext': r'ext',
    'm3u': r'(\.m3u8?)|(&?type=m3u8?)',
    'streams': r'(\.ts)|(\.mp4)|(\.mkv)|(\.ch)|(\.mpg)|(\/mpegts)|(stream\/channelid\/\d{1,14})|(\/udp\/'
                r'(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]):\d{4})|'
                r'(\/play\/[as]0?[\d\w]{1,2})|(\/live\?channelid)'
}

def request(url):
    try:
        r = requests.get(url, timeout=5)
    except (ConnectionError, ReadTimeout, TooManyRedirects, ChunkedEncodingError):
        pass
    else:
        if r.ok:
            return r


def parse_text(host):
    print('Parsing', host)
    r = request(host)
    if r:
        splitext = r.text.splitlines()
        for x in range(1, len(splitext)):
            print(splitext[x])
            url = splitext[x].strip()
            if re.search(regex['ext'], splitext[x - 1]) and not re.search(regex['ext'], splitext[x]):
                if re.search(regex['m3u'], url):
                    parse_text(url)
                elif re.search(regex['streams'], url):
                    #print('Adding %s' % url)
                    streams.append(url)
    print('Streams of %s %s' % (host, str(streams)))

