import pytest
from exceptions import *
from crawler import Crawler
import requester
import url_mutator as um
import re
import zipfile
from bs4 import BeautifulSoup
from database import HostList, Streamer
import socket
from bson import SON

# Requester method
# Tests that the validate_url method functions properly
def test_validate_url():
    url1 = 'https://www.reddit.com'
    url2 = 'www.reddit.com'
    url3 = None
    url4 = 'dog'
    url5 = 6
    url6 = []
    url7 = 'https://www.reddit.com'
    url8 = 'http://reddit.com/r/all'
    url9 = 'http://leaderpro.pt:25461/live/Andreia/Andreia/15182.ts'
    url10 = 'http://streamer1.streamhost.org:1935/salive/GMIalfah/chunklist.m3u8?'
    url11 = 'https://192.12.15.0/play/.ts'
    urls = [url1, url2, url3, url4, url5, url6, url7, url8, url9, url10, url11]
    valid_urls = []
    for url in urls:
        if requester.validate_url(url):
            valid_urls.append(url)

    assert valid_urls == [url1, url7, url8, url9, url10]

def test_remove_identifier():
    url1 = um.remove_identifier('http://www.reddit.com')
    url2 = um.remove_identifier('http://ramalin.com')
    url3 = um.remove_identifier('http://www.ramalin.com')
    url4 = um.remove_identifier('http://www.ip.akaid.com')

    assert url1 == 'http://reddit.com'
    assert url2 == url3 == 'http://ramalin.com'
    assert url4 == 'http://ip.akaid.com'

def error_check_remove_identifier():
    loc1 = None
    loc2 = []
    loc3 = 23
    loc4 = {}
    locs = [loc1, loc2, loc3, loc4]
    for loc in locs:
        with pytest.raises(InvalidUrlError):
            um.remove_identifier(loc)

# Requester method
# Tests that the internal method function properly
def test_internal():
    host1 = 'https://www.reddit.com'
    host2 = 'https://reddit.com/'

    def internal_func(base): # helper method
        url1 = 'https://www.reddit.com'
        url2 = 'https://reddit.com/r/aww'
        url3 = 'https://www.reddit.com/user/MzTriggerHappy'
        url4 = 'https://reddit.com/user/MzTriggerHappy/posts/'
        url5 = 'http://book.pythontips.com/en/latest/enumerate.html'
        url6 = 'https://www.jetbrains.com/help/idea/suppressing-inspections.html'
        urls = [url1, url2, url3, url4, url5, url6]
        internal_urls = []
        for url in urls:
            if requester.internal(url, base):
                internal_urls.append(url)

        assert internal_urls == [url1, url2, url3, url4]

    internal_func(host1)
    internal_func(host2)

# Requester method
# Error checks the internal method with invalid urls
def error_check_internal():
    url1 = None
    url2 = 23
    url3 = '//www.reddit.com'
    url4 = 'www.google.com'
    valid = 'http://www.reddit.com'
    urls = [url1, url2, url3, url4]
    for url in urls:
        with pytest.raises(InvalidUrlError):
            requester.internal(url, valid)
        with pytest.raises(InvalidUrlError):
            requester.internal(valid, url)

# Requester method
# Checks that the make_request method functions properly
def test_make_request():
    url1 = 'https://www.google.com'
    url2 = 'http://freedailyiptv.com/links/29-05-2018/SE_freedailyiptv.com.m3u'
    url3 = 'http://bestiptvsrv.tk:25461/get.php?username=anis&password=anis&type=m3u'  # this link should not work
    urls = [url1, url2, url3]
    valid_requests = []
    for url in urls:
        request = requester.make_request(url)
        if request is not None:
            valid_requests.append(url)

    assert valid_requests == [url1, url2]

# Requester method
# Error checks the make_request method with invalid urlsz
def error_check_make_request():
    url1 = None
    url2 = 23
    url3 = '//www.reddit.com'
    url4 = 'www.google.com'
    urls = [url1, url2, url3, url4]
    for url in urls:
        with pytest.raises(InvalidUrlError):
            requester.make_request(url)

# Requester method
# Checks the the get_format method functions properly
def test_get_format():
    request1 = requester.make_request('http://freedailyiptv.com/links/29-05-2018/SE_freedailyiptv.com.m3u')
    request2 = requester.make_request('http://freedailyiptv.com/links/11-06-2018/World_freedailyiptv.com.m3u')
    request3 = requester.make_request(
        'http://xsat.me:31000/get.php?username=mahmood&password=mahmood&type=m3u')  # not an m3u
    request4 = requester.make_request('https://dailyiptvlist.com/dl/us-m3uplaylist-2018-06-12-1.m3u')
    request5 = requester.make_request('https://cafe-tv.net/wp-content/uploads/2018/06/france0606.m3u')
    request6 = requester.make_request('http://ipv4.download.thinkbroadband.com/5MB.zip')
    request7 = requester.make_request('http://www.mediafire.com/file/opkx06qikkxetya/IPTV-Espa%C3%B1a-M3u-Playlist-'
                                 'Update-17-12-2017.zip')
    format1 = requester.get_format(request1)
    format2 = requester.get_format(request2)
    format3 = requester.get_format(request3)
    format4 = requester.get_format(request4)
    format5 = requester.get_format(request5)
    format6 = requester.get_format(request6)
    format7 = requester.get_format(request7)
    m3us = [format1, format2, format4, format5]
    zips = [format6]
    htmls = [format3, format7]
    for f in m3us:
        assert f == 'm3u', 'Error: incorrect format'
    for f in zips:
        assert f == 'zip', 'Error: incorrect format'
    for f in htmls:
        assert f == 'html', 'Error: incorrect format'

# Requester method
# Error checks the requester method with invalid urls
def error_check_get_format():
    request1 = None
    request2 = 23
    request3 = 'http//www.reddit.com'
    request4 = 'www.google.com'
    requests = [request1, request2, request3, request4]
    for request in requests:
        with pytest.raises(InvalidInputError):
            requester.get_format(request)

# Requester method
# Tests that the hash content method functions properly
def test_hash_content():
    def hash_unzip(f):
        z = zipfile.ZipFile(f)
        for info in z.infolist():
            f = z.read(info.filename)
            return f

    file1 = hash_unzip(r'C:\Users\pharvie\Desktop\Test Cases\America1.zip')
    file2 = hash_unzip(r'C:\Users\pharvie\Desktop\Test Cases\America2.zip')
    file3 = hash_unzip(r'C:\Users\pharvie\Desktop\Test Cases\Deutsch1.zip')
    file4 = hash_unzip(r'C:\Users\pharvie\Desktop\Test Cases\Deutsch2.zip')
    file5 = hash_unzip(r'C:\Users\pharvie\Desktop\Test Cases\Albania1.zip')
    file6 = hash_unzip(r'C:\Users\pharvie\Desktop\Test Cases\Albania2.zip')

    for f in [file1, file2]:
        assert requester.hash_content(f) == '10ea6d3d7b039039036ce85d58e37d7438b33662'
    for f in [file3, file4]:
        assert requester.hash_content(f) == '38708f813c47e93e9b23bb45c8f439d493a669de'
    for f in [file5, file6]:
        assert requester.hash_content(f) == '06af3dfa1ad9a1cc56331efa5bbb41e4a1c7b48e'

# Requester method
# Error checks the hash_content method with non-bytes input
def error_check_hash_content():
    file1 = None
    file2 = 23
    file3 = []
    file4 = open(r'C:\Users\pharvie\Desktop\Test Cases\America1.zip')
    for f in [file1, file2, file3, file4]:
        with pytest.raises(InvalidInputError):
            requester.hash_content(f)

# Requester method
# Tests that the subpaths method functions properly
def test_subpaths():
    url1 = 'http://reddit.com/r/all'
    url2 = 'http://reddit.com/r/all/'
    url3 = 'http://reddit.com/'
    url4 = 'http://reddit.com'
    urls = [url1, url2]
    for url in urls:
        subpaths = requester.subpaths(url)
        assert subpaths == ['r', 'all']

    urls = [url3, url4]
    for url in urls:
        subpaths = requester.subpaths(url)
        assert subpaths == []

# Requester method

def error_check_subpaths():
    url1 = None
    url2 = 23
    url3 = []
    url4 = 'www.reddit.com'
    urls = [url1, url2, url3, url4]
    for url in urls:
        with pytest.raises(InvalidUrlError):
            requester.subpaths(url)

def test_purity():
    purity1 = requester.purity('http://reddit.com/r/all')
    purity2 = requester.purity('http://reddit.com/u/capshockey/submitted')
    purity3 = requester.purity('http://reddit.com/2018/06/iptv-m3u-sport')
    purity4 = requester.purity('http://reddit.com/bqxon')
    purity5 = requester.purity('http://www.freshiptv.com/free-cccam-servers-world-cup')
    purity6 = requester.purity('http://reddit.com')

    assert purity1 == 100
    assert purity2 == 100
    assert abs(purity3 - 66.66666) < .0001
    assert purity4 == 100
    assert purity5 == 0
    assert purity6 == -1

def error_check_purity():
    sub1 = None
    sub2 = 23
    sub3 = set()
    sub4 = 'www.reddit.com'
    subs = [sub1, sub2, sub3, sub4]
    for sub in subs:
        with pytest.raises(InvalidUrlError):
            um.remove_top(sub)

def test_queries():
    url1 = 'https://www.list-iptv.com/search/label/Download%20iptv%20uk?&max-results=10'
    url2 = 'http://www.facebook.com/sharer.php?u=https://www.list-iptv.com/'
    url3 = 'https://i0.wp.com/cafe-tv.net/wp-content/uploads/2017/11/Extension-exodus-Repo-Addon-Kodi-install-3.jpg?fit=985%2C501&ssl=1'
    url4 = 'https://www.blogger.com/share-post.g?blogID=1041638923557619843&postID=3582939062652584883&target=twitter'
    url5 = 'http://kibuilder.com/RoG'
    url6 = 'http://adf.ly/HmtTG'
    url7 = 'http://rapidtory.com/1seI'
    url8 = 'http://www.reddit.com/r/all/fiteme'

    for url in [url1, url2, url3, url4]:
        assert requester.queries(url) == 1

    for url in [url5, url6, url7, url8]:
        assert requester.queries(url) == 0

def error_check_queries():
    url1 = None
    url2 = 23
    url3 = []
    url4 = 'www.reddit.com'
    urls = [url1, url2, url3, url4]
    for url in urls:
        with pytest.raises(InvalidUrlError):
            requester.queries(url)

def test_phrases():
    phrases1 = requester.phrases('http://www.reddit.com/r/all')
    phrases2 = requester.phrases('http://www.freshiptv.com/free-30-iptv-list-premium-worldsport-hd-sd-channels-m3u')
    phrases3 = requester.phrases('https://www.list-iptv.com/p/telecharger-iptv-france.html')
    phrases4 = requester.phrases('http://www.reddit.com')
    phrases5 = requester.phrases('https://www.list-iptv.com/search/label/IPTV%20England')

    assert phrases1 == ['r', 'all']
    assert phrases2 == ['free', 'iptv', 'list', 'premium', 'worldsport', 'hd', 'sd', 'channels', 'm3u']
    assert phrases3 == ['p', 'telecharger', 'iptv', 'france', 'html']
    assert phrases4 == []
    assert phrases5 == ['search', 'label', 'IPTV', 'England']

def error_check_phrases():
    url1 = None
    url2 = 23
    url3 = []
    url4 = 'www.reddit.com'
    urls = [url1, url2, url3, url4]
    for url in urls:
        with pytest.raises(InvalidUrlError):
            requester.phrases(url)

# requester method
# checks the return of the evaluate stream method 
def test_evaluate_stream():
    url1 = 'http://devcon101.com:8080/live/alican/10062018/33.ts' # doesn't work
    url2 = 'http://trexiptv.pointto.us:8000/live/spiderbox/c7eornHc3w/956.ts' # works
    url3 = 'http://54.37.255.204:9977/live/Rodriguez/Rodriguez/24720.ts' # works sometimes
    url4 = 'http://world-ipsat.com:1155/live/sultan/sultan2018/5209.ts' # works
    url5 = 'http://217.182.173.184:8000/live/micha/micha/492.ts' # doesn't work
    for url in [url1, url2, url3, url4, url5]:
        requester.evaluate_stream(url)


# url mutator method
# checks the return of the reduce method
def test_reduce():
    url1 = um.reduce('http://reddit.com/')
    url2 = um.reduce('http://reddit.com')

    assert url1 == url2

# url mutator method
# error checks the reduce method
def error_check_reduce():
    url1 = None
    url2 = 23
    url3 = '//www.reddit.com'
    url4 = 'www.google.com'
    urls = [url1, url2, url3, url4]
    for url in urls:
        with pytest.raises(InvalidUrlError):
            um.reduce(url)

def test_deport():
    url1 = um.deport('http://192.68.132.1:800')
    url2 = um.deport('http://132.100.12.1')
    url3 = um.deport('http://www.fattyport:80')
    url4 = um.deport('http://www.something:81')
    url5 = um.deport('http://www.otherthing')
    url6 = um.deport('http://s4.bossna-caffe.com:80/hls/1200.m3u8?channelId=1200&deviceMac='
                            '00:1A:79:3A:2D:B9&uid=35640')
    url7 = um.deport('http://s0.balkan-x.net:80/playlist?type=m3u&deviceMac=00:1A:79:3A:2D:B9')

    assert url1 == 'http://192.68.132.1'
    assert url2 == 'http://132.100.12.1'
    assert url3 == 'http://www.fattyport'
    assert url4 == 'http://www.something'
    assert url5 == 'http://www.otherthing'
    assert url6 == 'http://s4.bossna-caffe.com/hls/1200.m3u8?channelId=1200&deviceMac=00:1A:79:3A:2D:B9&uid=35640'
    assert url7 == 'http://s0.balkan-x.net/playlist?type=m3u&deviceMac=00:1A:79:3A:2D:B9'

def error_check_deport():
    url1 = None
    url2 = 23
    url3 = []
    url4 = 'www.reddit.com'
    for url in [url1, url2, url3, url4]:
        with pytest.raises(InvalidUrlError):
            um.deport(url)

def test_remove_top():
    domain1, top1 = um.remove_top('http://www.reddit.com/r/all')
    domain2, top2 = um.remove_top('http://www.ak-ahmaid.1up.next.com/anythinggoes')
    domain3, top3 = um.remove_top('http://bit.ly/AWEr')
    domain4, top4 = um.remove_top('https://goo.gl/x6khNK')

    assert domain1 == 'reddit'
    assert top1 == top2 == 'com'
    assert domain2 == 'ak-ahmaid.1up.next'
    assert domain3 == 'bit'
    assert top3 == 'ly'
    assert domain4 == 'goo'
    assert top4 == 'gl'

def error_check_remove_top():
    url1 = None
    url2 = 23
    url3 = []
    url4 = 'www.reddit.com'
    urls = [url1, url2, url3, url4]
    for url in urls:
        with pytest.raises(InvalidUrlError):
            um.remove_top(url)

def test_remove_schema():
    url1 = um.remove_schema('http://reddit.com')
    url2 = um.remove_schema('https://www.reddit.com/r/all?fat=True&not%20fat=False')
    url3 = um.remove_schema('http://facebook.com')

    assert url1 == 'reddit.com'
    assert url2 == 'www.reddit.com/r/all?fat=True&not%20fat=False'
    assert url3 == 'facebook.com'

def error_check_remove_schema():
    url1 = None
    url2 = 23
    url3 = []
    url4 = 'www.reddit.com'
    urls = [url1, url2, url3, url4]
    for url in urls:
        with pytest.raises(InvalidUrlError):
            um.remove_schema(url)

def test_prepare_netloc():
    url1 = um.prepare_netloc('http://s4.bossna-caffe.com:80/hls/1200.m3u8?channelId=1200&deviceMac=00:1A:79:3A:2D:B9&uid=35640')
    url2 = um.prepare_netloc('http://www.s4.bossna-caffe.com:80/hls/1200.m3u8?channelId=1200&deviceMac=00:1A:79:3A:2D:B9&uid=35640/')
    url3 = um.prepare_netloc('http://192.68.132.1:800')
    url4 = um.prepare_netloc('http://192.68.132.1:400')
    url5 = um.prepare_netloc('http://www.soledge7.dogannet.tv/S1/HLS_LIVE/tv2/1000/prog_index.m3u8')
    url6 = um.prepare_netloc('http://soledge7.dogannet.tv/S1/HLS_LIVE/tv2/1000/prog_index.m3u8')
    url7 = um.prepare_netloc('http://reddit.com')

    assert url1 == url2 == 'http://s4.bossna-caffe.com'
    assert url3 == url4 == 'http://192.68.132.1'
    assert url5 == url6 == 'http://soledge7.dogannet.tv'
    assert url7 == 'http://reddit.com'

def error_check_prepare_netloc():
    url1 = None
    url2 = 23
    url3 = '//www.reddit.com'
    url4 = 'www.google.com'
    urls = [url1, url2, url3, url4]
    for url in urls:
        with pytest.raises(InvalidUrlError):
            um.prepare_netloc(url)

# url mutator method method
# checks the return of the partial method
def test_partial():
    host = 'https://www.reddit.com'
    url1 = um.partial('//www.reddit.com', host)
    url2 = um.partial('/r/aww/top', host)
    url3 = um.partial('https://www.reddit.com/r/aww', host)
    url4 = um.partial('//www.facebook.com', host)
    url5 = um.partial('/r/MemeEconomy/comments/8or7ar/i_see_limited_potential_but_possible_useful/', host)
    url6 = um.partial('//reddit.com/r/all', host)
    url7 = um.partial('http://reddit.com/r/all', host)
    assert url1 == 'https://www.reddit.com'
    assert url2 == 'https://www.reddit.com/r/aww/top'
    assert url3 == 'https://www.reddit.com/r/aww'
    assert url4 == 'https://www.facebook.com'
    assert url5 == 'https://www.reddit.com/r/MemeEconomy/comments/8or7ar/i_see_limited_potential_but_possible_useful/'
    assert url6 == 'https://reddit.com/r/all'
    assert url7 == 'http://reddit.com/r/all'

# url mutator method
# error checks the partial method
def error_check_partial():
    host = 'https://www.reddit.com'
    url1 = None
    url2 = 23
    url3 = []
    urls = [url1, url2, url3]
    for url in urls:
        with pytest.raises(InvalidInputError):
            um.partial(url, host)
    for url in urls:
        with pytest.raises(InvalidHostError):
            um.partial(host, url)

# url mutator method
# checks the return of the phish method
def test_phish():
    url1 = um.phish('http://198.255.114.218:8000/get.php?username=j9&password;=j9&type;=m3u')
    url2 = um.phish('http://iptv.alkaicerteams.com:8080/get.php?username=alkaicer_66m62772&password;='
                           '3bjwn4c6&type;=m3u')
    url3 = um.phish('http://www.reddit.com/abc;def')
    url4 = um.phish('http://iptvurllist.com/upload/file/2016-03-27IPTV Italy Channels url Links.m3u')
    assert url1 == 'http://198.255.114.218:8000/get.php?username=j9&password=j9&type=m3u'
    assert url2 == 'http://iptv.alkaicerteams.com:8080/get.php?username=alkaicer_66m62772&password=3bjwn4c6&type=m3u'
    assert url3 == 'http://www.reddit.com/abc;def'
    assert url4 == 'http://iptvurllist.com/upload/file/2016-03-27IPTV%20Italy%20Channels%20url%20Links.m3u'

# url mutator method
# error checks the phish method
def error_check_phish():
    url1 = None
    url2 = 23
    urls = [url1, url2]
    for url in urls:
        with pytest.raises(InvalidInputError):
            um.phish(url)

# url mutator method
# checks the return of the expand method
def test_expand():
    url1 = um.expand('https://www.reddit.com')
    url2 = um.expand('https://bit.ly/1f3xnd9')  # https://www.reddit.com/r/all
    url3 = um.expand('https://bitly.com/')
    url4 = um.expand('https://bit.ly/188dxN0')  # https://www.facebook.com
    url5 = um.expand('https://ift.tt/2GnlsZS')
    url6 = um.expand('https://goo.gl/Nc38rb')
    assert url1 == 'https://www.reddit.com'
    assert re.search(r'https:\/\/www.reddit.com\/r\/all\/?', url2) is not None
    assert url3 == 'https://bitly.com/'
    assert url4 == 'https://www.facebook.com/'
    assert url5 == 'http://163.172.51.84:25461/live/superiptv1/superiptv111/21523.ts'
    assert requester.host(url6) == 'https://doc-10-50-docs.googleusercontent.com'

# url mutator method
# error checks the expand method
def error_check_expand():
    url1 = None
    url2 = 23
    url3 = '//www.reddit.com'
    url4 = 'www.google.com'
    urls = [url1, url2, url3, url4]
    for url in urls:
        with pytest.raises(InvalidUrlError):
            um.expand(url)

def test_reduce_queries():
    url1 = um.reduce_queries('https://www.list-iptv.com/search?updated-max=2018-03-31T21:55:00%2B02:00&max-results=20')
    url2 = um.reduce_queries('https://www.list-iptv.com/search?updated-max=2018-03-31T21:55:00%2B02:00&max-results=40')
    url3 = um.reduce_queries('http://iptvsatlinks.blogspot.com/search/sports%20tv?updated-max=2016-02-17T11:53:00-08:00&max-results=20')
    url4 = um.reduce_queries('http://iptvsatlinks.blogspot.com/search/label/Germany?updated-max=2018-06-21T03:10:00-07:00&by-date=false')
    url5 = um.reduce_queries('https://www.list-iptv.com/search?updated-max=2018-03-20T23:52:00%2B01:00&max-results=20&by-date=false')
    url6 = um.reduce_queries('https://www.list-iptv.com/search/iptv%20playlist%202018?updated-max=2018-07-06T13:36:00%2B02:00&start=20')
    url7 = um.reduce_queries('https://cafe-tv.net/wp-login.php?action=lostpassword&redirect_to='
                             'https%3A%2F%2Fcafe-tv.net%2F2017%2F05%2Fiptv-m3u-spain-channels-list-spain-m3u-vlc-02-05-17%2F')
    url8 = um.reduce_queries('https://cafe-tv.net/wp-login.php?action=lostpassword&redirect_to='
                             'https%3A%2F%2Fcafe-tv.net%2Fauthor%2Fkais-jemmali%2Fpage%2F64%2F')

    assert url1 == url2 == 'https://www.list-iptv.com/search'
    assert url3 == 'http://iptvsatlinks.blogspot.com/search/sports%20tv'
    assert url4 == 'http://iptvsatlinks.blogspot.com/search/label/Germany'
    assert url5 == 'https://www.list-iptv.com/search'
    assert url6 == 'https://www.list-iptv.com/search/iptv%20playlist%202018'
    assert url7 == url8 == 'https://cafe-tv.net/wp-login.php'

# HostList method
# tests that the add_to_hosts method functions properly
def test_add_to_hosts():
    host_list = HostList('test_add_to_hosts')
    host1 = 'http://list-iptv.com'
    host2 = 'http://ramalin.com'
    host3 = 'http://m3uliste.com'
    for host in [host1, host2, host3]:
        host_list.add_to_hosts(host)
        assert host_list.database().hosts.find({'host': host}) is not None

    host_list.delete()

# HostList method
# error checks the host list method
def error_check_add_to_hosts():
    host_list = HostList('error_check_add_to_hosts')
    host = 'http://list-iptv.com'
    host_list.database().hosts.insert({'host': host, 'running': False})
    with pytest.raises(EntryInDatabaseError):
        host_list.add_to_hosts(host)

    for invalid in [[], set(), 'fat', 'reddit.com']:
        with pytest.raises(InvalidUrlError):
            host_list.add_to_hosts(invalid)

    host_list.delete()

# HostList method
# tests that entry_from_host method functions properly
def test_entry_from_host():
    host_list = HostList('test_entry_from_host')
    host1 = 'http://list-iptv.com'
    host2 = 'http://ramalin.com'
    host3 = 'http://m3uliste.com'
    for host in [host1, host2, host3]:
        host_list.add_to_hosts(host)
        entry = host_list.entry_from_host(host)
        assert entry is not None
        assert entry['host'] == host
        assert entry['running'] is False

    host_list.delete()

# HostList method
# error checks the entry_from_host method
def error_check_entry_from_host():
    host_list = HostList('error_check_entry_from_host')
    host = 'http://list-iptv.com'
    host_list.database().hosts.insert({'host': host, 'running': False})
    host_list.database().hosts.insert({'host': host, 'running': False})
    with pytest.raises(MultipleEntriesInDatabaseError):
        host_list.entry_from_host(host)

    for invalid in [[], set(), 'fat', 'reddit.com']:
        with pytest.raises(InvalidUrlError):
            host_list.entry_from_host(invalid)

    host_list.delete()

# HostList method
# tests that find_not_running_entry method functions properly
def test_find_not_running_entry():
    host_list = HostList('test_find_not_running_entry')
    host1 = 'http://list-iptv.com'
    host2 = 'http://ramalin.com'
    host3 = 'http://m3uliste.com'
    host_list.add_to_hosts(host1, True)

    assert host_list.find_not_running_entry() is None

    host_list.add_to_hosts(host2, False)
    host_list.add_to_hosts(host3, False)

    assert host_list.find_not_running_entry()['host'] == host2

    host_list.delete()

# HostList method
# tests that the update_running method functions properly
def test_update_running():
    host_list = HostList('test_update_running')
    host1 = 'http://list-iptv.com'
    host2 = 'http://ramalin.com'
    host3 = 'http://m3uliste.com'
    for host in [host1, host2, host3]:
        host_list.add_to_hosts(host)

    order = []

    while host_list.find_not_running_entry() is not None:
        entry = host_list.find_not_running_entry()
        host = entry['host']
        host_list.update_running(host, True)
        order.append(host)

    for host in [host1, host2, host3]:
        assert host_list.entry_from_host(host)['running'] is True

    assert order == [host1, host2, host3]

    host_list.delete()

# HostList method
# error checks the update_running method
def error_check_update_running():
    host_list = HostList('error_check_update_running')
    host = 'http://list-iptv.com'
    with pytest.raises(EntryNotInDatabaseError):
        host_list.update_running(host, True)

    for invalid in [[], set(), 'fat', 'reddit.com']:
        with pytest.raises(InvalidUrlError):
            host_list.update_running(invalid, True)

    host_list.delete()

# Streamer method
# Error checks the initialization of the streamer class, which takes a string as input
def error_check_init_streamer():
    for invalid in [[], 0, None, set()]:
        with pytest.raises(InvalidInputError):
            Streamer(invalid)

# Streamer method
# Checks that the document_from_ip_address method functions properly
def test_document_from_ip_address():
    streamer = Streamer('test_document_from_ip_address')
    host = 'http://list-iptv.com'
    url1 = 'http://62.210.245.19:8000/live/testapp/testapp/2.ts'
    url2 = 'http://clientportalpro.com:2500/live/VE5DWv4Ait/7KHLqRRZ9E/2160.ts'
    url3 = 'http://ndasat.pro:8000/live/exch/exch/1227.ts'
    for url in [url1, url2, url3]:
        netloc = um.prepare_netloc(url)
        ip_addresses = socket.gethostbyname_ex(um.remove_schema(netloc))[2]
        for ip_address in ip_addresses:
            data = {
                'ip_address': ip_address,
                'network_locations': [SON([('network_location', netloc), ('linked_by', [host]), ('working_link', True)])]
            }
            streamer.collection().insert(data)
            doc = streamer.document_from_ip_address(ip_address)
            assert doc['ip_address'] == ip_address
            assert doc['network_locations'] == [SON([('network_location', netloc), ('linked_by', [host]), ('working_link', True)])]

    streamer.delete()

# Streamer method
# Error checks document_from_ip_address with an invalid IP address
def error_check_document_ip_address_with_invalid_ips():
    streamer = Streamer('error_check_document_ip_address_with_invalid_ip')
    for invalid in ['192.68.90.1.1', '1456.2435.5425.788', 'fat cat', 'totally not an ip address']: # invalid IP addresses
        with pytest.raises(InvalidInputError):
            streamer.document_from_ip_address(invalid)

# Streamer method
# Tests that the entry_from_netloc method functions properly
def test_entry_from_netloc():
    streamer = Streamer('test_entry_from_netloc')
    host = 'http://ramalin.com'
    netloc1 = 'http://gameriptv.com'
    netloc2 = 'http://164.132.136.176'
    netloc3 = 'http://31.132.0.66'
    netloc4 = 'http://reddit.com'
    netloc5 = 'http://facebook.com'
    for netloc in [netloc1, netloc2, netloc3]:
        ip_addresses = socket.gethostbyname_ex(um.remove_schema(netloc))[2]
        for ip_address in ip_addresses:
            data = {
                'ip_address': ip_address,
                'network_locations': [SON([('network_location', netloc), ('linked_by', [host]), ('working_link', True)])]
            }
            streamer.collection().insert(data)
            doc = streamer.document_from_ip_address(ip_address)
            entry = streamer.entry_from_netloc(doc, netloc)
            assert entry is not None
            assert entry['network_location'] == netloc
            assert entry['linked_by'] == [host]
            assert entry['working_link'] is True
            assert streamer.entry_from_netloc(doc, netloc4) is None
            assert streamer.entry_from_netloc(doc, netloc5) is None

    streamer.delete()

# Streamer method
# Error checks the entry_from_netloc method with a null document
def error_check_entry_from_netloc_with_null_doc():
    streamer = Streamer('error_check_entry_from_netloc_with_null_doc')
    netloc = 'http://reddit.com'
    with pytest.raises(InvalidInputError):
        streamer.entry_from_netloc(None, netloc)

# Streamer method
# Error checks the entry_from_netloc method with invalid urls
def error_check_entry_from_netloc_with_invalid_urls():
    streamer = Streamer('error_check_entry_from_netloc_with_invalid_urls')
    doc = {}
    for invalid in [[], set(), 0, 'www.reddit.com']:
        with pytest.raises(InvalidUrlError):
            streamer.entry_from_netloc(doc, invalid)

# Streamer method
# Tests that the add_to_database_by_ip_address method functions properly when adding an ip address that has not yet occurred
def test_add_to_database_by_ip_address():
    streamer = Streamer('test_add_to_database_by_ip_address')
    host = 'http://list-iptv.com'
    url1 = 'http://62.210.245.19:8000/live/testapp/testapp/2.ts'
    url2 = 'http://clientportalpro.com:2500/live/VE5DWv4Ait/7KHLqRRZ9E/2160.ts'
    url3 = 'http://ndasat.pro:8000/live/exch/exch/1227.ts'
    for url in [url1, url2, url3]:
        netloc = um.prepare_netloc(url)
        ip_addresses = socket.gethostbyname_ex(um.remove_schema(netloc))[2]
        for ip_address in ip_addresses:
            streamer.add_to_database_by_ip_address(ip_address, netloc, host, None)
            doc = streamer.document_from_ip_address(ip_address)

            assert doc['ip_address'] == ip_address
            for entry in doc['network_locations']:
                assert entry['network_location'] == netloc

    streamer.delete()

# Streamer method
# Tests that the add_to_database_by_ip_address method functions properly when adding an ip address already present in the database, and
# the netloc is not currently present in the document
def test_add_to_document_by_ip_address_with_netloc_not_in_document():
    streamer = Streamer('test_add_to_document_by_ip_address_with_netloc_not_in_document')
    host = 'http://list-iptv.com'
    url1 = 'http://62.210.245.19'
    url2 = 'http://clientportalpro.com'
    url3 = 'http://ndasat.pro'
    for url in [url1, url2, url3]:
        ip_address = '192.168.32.1'
        streamer.add_to_database_by_ip_address(ip_address, url, host, True)

    doc = streamer.document_from_ip_address(ip_address)
    assert doc['ip_address'] == ip_address
    assert doc['network_locations'] == [
        SON([('network_location', url1), ('working_link', True)]),
        SON([('network_location', url2), ('working_link', True)]),
        SON([('network_location', url3), ('working_link', True)])
    ]

    streamer.delete()
    
# Streamer method
# Tests that the add_to_database_by_ip_address method functions properly when adding an ip address and network location already present 
# in the database, and the host is not currently present in the linked_by of the document
def test_add_to_document_by_ip_address_with_host_not_in_linked_by():
    streamer = Streamer('test_add_to_document_by_ip_address_with_host_not_in_linked_by')
    netloc = 'http://reddit.com'
    host1 = 'http://list-iptv.com'
    host2 = 'http://ramalin.com'
    host3 = 'http://m3uliste.com'
    host4 = 'http://list-iptv.com'
    ip_addresses = socket.gethostbyname_ex(um.remove_schema(netloc))[2]
    for ip_address in ip_addresses:
        for host in [host1, host2, host3, host4]:
            streamer.add_to_database_by_ip_address(ip_address, netloc, host, True)
        doc = streamer.document_from_ip_address(ip_address)
        assert doc['ip_address'] == ip_address
        assert doc['linked_by'] == [host1, host2, host3]

    streamer.delete()

# Streamer method
# Test that the add_to_document_by_ip_address correctly updates the working_link status of a netloc at an ip_address
def test_update_working_link_of_add_to_document_by_ip_address():
    streamer = Streamer('test_update_working_link')
    netloc1 = 'http://reddit.com'
    netloc2 = 'http://facebook.com'
    netloc3 = 'http://ramalin.com'
    host = 'http://list-iptv.com'
    ip_address1 = '192.68.12.1'
    ip_address2 = '192.68.12.2'
    ip_address3 = '192.68.12.3'
    ip_address4 = '192.68.12.4'
    ip_address5 = '192.68.12.5'
    for netloc in [netloc1, netloc2, netloc3]:
        # None to True
        streamer.add_to_database_by_ip_address(ip_address1, netloc, host, None)
        streamer.add_to_database_by_ip_address(ip_address1, netloc, host, True)
        efn = streamer.entry_from_netloc(streamer.document_from_ip_address(ip_address1), netloc)
        assert efn['working_link'] is True
        # False to True
        streamer.add_to_database_by_ip_address(ip_address2, netloc, host, False)
        streamer.add_to_database_by_ip_address(ip_address2, netloc, host, True)
        efn = streamer.entry_from_netloc(streamer.document_from_ip_address(ip_address2), netloc)
        assert efn['working_link'] is True
        # None to False
        streamer.add_to_database_by_ip_address(ip_address3, netloc, host, None)
        streamer.add_to_database_by_ip_address(ip_address3, netloc, host, False)
        efn = streamer.entry_from_netloc(streamer.document_from_ip_address(ip_address3), netloc)
        assert efn['working_link'] is False
        # Not False to True
        streamer.add_to_database_by_ip_address(ip_address4, netloc, host, True)
        streamer.add_to_database_by_ip_address(ip_address4, netloc, host, False)
        efn = streamer.entry_from_netloc(streamer.document_from_ip_address(ip_address4), netloc)
        assert efn['working_link'] is True
        # Not None to False
        streamer.add_to_database_by_ip_address(ip_address5, netloc, host, False)
        streamer.add_to_database_by_ip_address(ip_address5, netloc, host, None)
        efn = streamer.entry_from_netloc(streamer.document_from_ip_address(ip_address5), netloc)
        assert efn['working_link'] is False

    streamer.delete()

# tester method
# A helper method that takes in a list of urls, creates a test helper for each url, and concatenates the streams found
# at each url based on the inputted method
def crawler_helper(urls, method='check_for_files'):
    streams = set()
    for url in urls:
        crawler = Crawler(test_url=url)
        if method is 'check_for_files':
            crawler.check_for_files(url)
        elif method is 'text':
            r = requester.make_request(url)
            if r:
                soup = BeautifulSoup(r.text, 'html.parser')
                crawler.check_text_urls(soup, r.url)
        elif method is 'ref':
            r = requester.make_request(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            crawler.check_ref_urls(soup)
        for post in crawler.get_streamer().database().streams.find():
            for netloc in post['network_locations']:
                streams.add(netloc['network_location'])
        crawler.streamer.delete()
    return streams

# Crawler method
# Tests that the crawler correctly parse m3us
def test_parse_with_m3u():
    url1 = um.expand('https://bit.ly/2t05257')
    url2 = 'https://www.dailyiptvlist.com/dl/pt-m3uplaylist-2018-06-11.m3u'
    url3 = 'http://premium-iptv.link:6969/get.php?username=despina&password=despina&type=m3u'
    url4 = 'https://cafe-tv.net/wp-content/uploads/2017/05/italia090501.m3u'
    url5 = 'http://iptvurllist.com/upload/file/2017-07-29Iptv-France-Server-Playlist-Url-Link-m3u-29-07.m3u'
    url6 = 'https://cafe-tv.net/wp-content/uploads/2018/07/france0107.m3u'
    url7 = 'https://adultswim-vodlive.cdn.turner.com/live/daily_animated_1/stream_3.m3u8'
    url8 = 'https://cafe-tv.net/wp-content/uploads/2017/12/greek1612a.m3u'
    urls = [url1, url2, url3, url4, url5, url6, url7, url8]
    streams = crawler_helper(urls)

    assert 'http://190.2.138.101' in streams
    assert 'http://premium-iptv.link' in streams
    assert 'http://maxtvv.abdou123.com' in streams
    assert 'http://rmd.primatv.club' in streams
    assert 'http://tv.primatv.club' in streams
    assert 'http://maxtvv.abdou123.com' in streams
    assert 'http://145.239.1.103' in streams
    assert 'https://adultswim-vodlive.cdn.turner.com' in streams
    assert 'http://82.192.84.30' in streams
    assert 'http://streamer-cache.grnet.gr' in streams

# Crawler method
# Tests that hte crawler correctly parses m3us from download files
# NOTE: all three of these files contain streams that do not have defined extensions
def test_parse_with_download():
    url1 = 'http://173.56.74.197:9981/playlist/channels'
    url2 = 'http://182.218.222.224:9981/playlist'
    url3 = 'https://drive.google.com/uc?export=download&id=1kNL8nfRL1F0x52wYZ9uJC98aElpqIntw'
    url4 = 'https://drive.google.com/uc?export=download&id=17xs13weC42ZudxkAH_LNBeCR3R0IX_F8'
    urls = [url1, url2, url3, url4]
    streams = crawler_helper(urls)

    assert 'http://173.56.74.197' in streams
    assert 'http://182.218.222.224' in streams
    assert 'http://xtv.satarabia.com' in streams
    assert 'http://164.132.200.17' in streams

# Crawler method
# Tests that the crawler correctly parses m3us from zip files
def test_parse_with_zip():
    url1 = 'http://www.mediafire.com/file/opkx06qikkxetya/IPTV-Espa%C3%B1a-M3u-Playlist-Update-17-12-2017.zip'
    url2 = 'https://www.mediafire.com/file/mjvk5vrarb39q8e/IPTV-Turkish-M3u-Channels-Update-04-12-2017.zip'
    url3 = 'https://www.colorado.edu/conflict/peace/download/peace_treatment.ZIP'
    url4 = 'http://download1586.mediafire.com/zat78d8fdnkg/0dpgto94u7q74r4/IPTV-M3u-Sport-All-Channels-List-17-12-2017.zip'
    url5 = 'http://www.mediafire.com/file/bu19timjoao110c/IPTV-Espa%C3%B1a-M3u-Playlist-Update-12-12-2017.zip' # works with utf-8 is none
    url6 = 'http://www.mediafire.com/file/rrpvrj0rdgealj4/IPTV-Turk-M3u-Playlist-Update-12-12-2017.zip' # same thing
    urls = [url1, url2, url3, url4, url5, url6]
    streams = crawler_helper(urls)

    assert 'http://proxiiptv.com' in streams
    assert 'http://skynet-iptv.dyndns.tv' in streams
    assert 'http://topiptv.net' in streams
    assert 'http://clientportal.link' in streams
    assert 'http://xtreme.webhop.me' in streams
    assert 'http://universeiptv.com' in streams
    assert 'http://x-media.tv' in streams
    assert 'http://nasaiptv.com' in streams
    assert 'http://globiptv.com' in streams
    assert 'http://biloiptv.eu.com' in streams

# Crawler method
# Tests that the crawler correctly opens m3u files it finds while parsing an m3u file
def test_parse_text_from_parse():
    url1 = 'http://www.mediafire.com/file/35txqby0vtpzvva/IPTV+World+Mix+M3u+.Update+All+Channels+21-11-2017.m3u'
    url2 = 'http://dwstream4-lh.akamaihd.net/i/dwstream4_live@131329/master.m3u8'
    url3 = 'http://theblaze.global.ssl.fastly.net/live/blaze-dvr/master.m3u8'  # also contains relatives
    urls = [url1, url2, url3]
    streams = crawler_helper(urls)

    assert 'http://wms.shared.streamshow.it' in streams
    assert 'http://37.187.142.147' in streams
    assert 'http://cremona1.econcept.it' in streams
    assert 'http://wow01.105.net' in streams
    assert 'http://skyianywhere2-i.akamaihd.net' in streams
    assert 'http://dwstream4-lh.akamaihd.net' in streams
    assert 'http://theblaze.global.ssl.fastly.net' in streams

# Crawler method
# Tests that the crawler correctly opens relative urls found while parsing an m3u file
def test_parse_with_relatives():
    url1 = 'http://soledge7.dogannet.tv/S1/HLS_LIVE/tv2/1000/prog_index.m3u8'  # ts files only
    url2 = 'https://ucankus-live.cdnnew.com/ucankus/ucankus.m3u8'  # ts files only
    url3 = 'http://publish.thewebstream.co:1935/studio66tv/_definst_/studio66tv_channel11/playlist.m3u8'  # m3u file
    url4 = 'http://bqgsd19q.rocketcdn.com/kralpop_720/chunklist.m3u8'  # ts files only
    url5 = 'http://turkmedya.radyotvonline.com/turkmedya/ligradyo.stream/chunklist_w1493895268.m3u8'
    urls = [url1, url2, url3, url4, url5]
    streams = crawler_helper(urls)
    
    assert 'http://soledge7.dogannet.tv' in streams
    assert 'https://ucankus-live.cdnnew.com' in streams
    assert 'http://publish.thewebstream.co' in streams
    assert 'http://bqgsd19q.rocketcdn.com' in streams

# Crawler method
# Tests the crawler correctly finds and parses m3u and ts files in the text of a web page
def test_text_urls():
    url1 = 'http://iptvurllist.com/view_article.php?id=428-Iptv-France-Server-Playlist-Url-Link-m3u-29-07.html'  # ts
    url2 = 'http://www.ramalin.com/iptv-russian-tv-channels-playlist-12-06-2018/'  # ts
    url3 = 'https://www.dailyiptvlist.com/italy-iptv-m3u-playlist-download-14-jun-2018/'  # m3us
    url4 = 'http://www.ramalin.com/poland-iptv-channels-playlist-07-06-2018/'  # ts segments
    url5 = 'http://www.iptvm3u.com/2018/03/iptv-england-server-m3u-list-update-02.html' # ts
    url6 = 'http://freeworldwideiptv.com/2018/06/19/germany-smart-tv-xbmc-iptv-m3u-playlist-19-06-2018/' # ts
    urls = [url1, url2, url3, url4, url5, url6]
    streams = crawler_helper(urls, 'text')

    assert 'http://62.210.245.19' in streams
    assert 'http://95.47.66.243' in streams
    assert 'http://217.182.173.184' in streams
    assert 'http://193.200.164.171' in streams
    assert 'http://vismanx1.com' in streams
    assert 'http://163.172.222.83' in streams
    assert 'http://91.123.176.105' in streams
    assert 'http://gigaiptv.tk' in streams
    assert 'http://145.239.205.121' in streams

# Crawler method
# Tests that the crawler correctly finds and parses m3u files from the referenced url of a webpage
def test_ref_urls():
    url1 = 'https://cafe-tv.net/2018/06/iptv-m3u-sport-speciale-coupe-du-monde-russie-2018'
    url2 = 'https://freedailyiptv.com/usa-m3u-free-daily-iptv-list-18-06-2018'
    url3 = 'http://iptvurllist.com/download.php?id=148-IPTV-Playlist-Deutsche-Germany-Links-Ts.html'
    urls = [url1, url2, url3]
    streams = crawler_helper(urls, 'ref')

    assert 'http://51.15.199.82' in streams
    assert 'http://sunatv.co' in streams
    assert 'http://185.71.66.108' in streams
    assert 'http://185.2.83.231' in streams
    assert 'http://212.8.250.12' in streams
    assert 'http://mypanel.tv' in streams
    assert 'http://hdreambox.dyndns.info' in streams

def requester_tests():
    return [test_validate_url, test_internal, error_check_internal, test_make_request, error_check_make_request, test_get_format,
            error_check_get_format, test_hash_content, error_check_hash_content, test_subpaths, error_check_subpaths, test_purity,
            error_check_purity, test_phrases, error_check_phrases]

def url_mutator_tests():
    return [test_reduce, error_check_reduce, test_remove_identifier, error_check_remove_identifier, test_deport, error_check_deport,
            test_remove_top, error_check_remove_top, test_remove_schema, error_check_remove_schema, test_prepare_netloc,
            error_check_prepare_netloc, test_partial, error_check_partial, test_phish, error_check_phish, error_check_expand]

def host_list_tests():
    return [test_add_to_hosts, error_check_add_to_hosts, test_entry_from_host, error_check_entry_from_host, test_find_not_running_entry,
            test_update_running, error_check_update_running]

def streamer_tests():
    return [error_check_init_streamer, test_document_from_ip_address, error_check_document_ip_address_with_invalid_ips,
            test_entry_from_netloc, error_check_entry_from_netloc_with_null_doc, error_check_entry_from_netloc_with_invalid_urls,
            test_add_to_database_by_ip_address, test_add_to_document_by_ip_address_with_netloc_not_in_document,
            test_add_to_document_by_ip_address_with_host_not_in_linked_by]

def crawler_tests():
    return [test_parse_with_m3u, test_parse_with_download, test_parse_with_zip, test_parse_text_from_parse,
            test_parse_with_relatives, test_text_urls, test_ref_urls]

def get_tests():
    return requester_tests() + url_mutator_tests() + crawler_tests()


def test_runner():
    for test in streamer_tests():
        print(test.__name__)
        test()


if __name__ == "__main__":
    print('Running tests...')
    test_runner()
    print('All tests passed!')
