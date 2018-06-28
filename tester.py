import pytest
from exceptions import InvalidURLException, InvalidHostException, InvalidRequestException, InvalidInputException, EmptyQueueException
from crawler import Crawler
import requester
import fixer
from node import Node
from my_queue import Queue
import re
import zipfile
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def test_validate():
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
    urls = [url1, url2, url3, url4, url5, url6, url7, url8, url9, url10]
    valid_urls = []
    for url in urls:
        if requester.validate(url):
            valid_urls.append(url)

    assert valid_urls == [url1, url7, url8, url9, url10], 'Error: Invalid urls in valid urls'


def test_host():
    url1 = 'http://www.reddit.com/r/all'
    url2 = 'http://www.reddit.com/r/aww'
    url3 = 'http://leaderpro.pt:25461/live/Andreia/Andreia/15095.ts'
    url4 = 'http://leaderpro.pt:25461/live/Andreia/Andreia/15182.ts'
    url5 = 'http://185.2.83.60:8080/live/mark/mark1/550.ts#EXTINF:-1,UK'
    url6 = 'http://185.2.83.60:8080/live/aurelio/aurelio/693.ts#EXTINF:-1,IT'
    assert requester.host(url1) == 'http://www.reddit.com', 'Error: incorrect host for url'
    assert requester.host(url1) == requester.host(url2), 'Error: hosts of links do not match'
    assert requester.host(url3) == 'http://leaderpro.pt:25461', 'Error: incorrect host for url'
    assert requester.host(url3) == requester.host(url4), 'Error: host of links do not match'
    assert requester.host(url5) == 'http://185.2.83.60:8080', 'Error: incorrect host for url'
    assert requester.host(url5) == requester.host(url6), 'Error: host of links do not match'


def error_check_host():
    url1 = None
    url2 = 23
    url3 = '//www.reddit.com'
    url4 = 'www.google.com'
    urls = [url1, url2, url3, url4]
    for url in urls:
        with pytest.raises(InvalidURLException):
            requester.host(url)


def test_remove_identifier():
    loc1 = requester.remove_identifier('www.reddit.com')
    loc2 = requester.remove_identifier('ramalin.com')
    loc3 = requester.remove_identifier('www2.ramalin.com')

    assert loc1 == 'reddit.com'
    assert loc2 == 'ramalin.com'
    assert loc3 == 'ramalin.com'


def error_check_remove_identifier():
    loc1 = None
    loc2 = []
    loc3 = 23
    loc4 = {}
    locs = [loc1, loc2, loc3, loc4]
    for loc in locs:
        with pytest.raises(InvalidInputException):
            requester.remove_identifier(loc)


def test_internal():
    url1 = 'https://www.reddit.com'
    url2 = 'https://reddit.com/'

    def internal_func(base):
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

    internal_func(url1)
    internal_func(url2)


#my_requester

def error_check_internal():
    url1 = None
    url2 = 23
    url3 = '//www.reddit.com'
    url4 = 'www.google.com'
    valid = 'http://www.reddit.com'
    urls = [url1, url2, url3, url4]
    for url in urls:
        with pytest.raises(InvalidURLException):
            requester.internal(url, valid)
        with pytest.raises(InvalidURLException):
            requester.internal(valid, url)


def test_request():
    url1 = 'https://www.google.com'
    url2 = 'http://freedailyiptv.com/links/29-05-2018/SE_freedailyiptv.com.m3u'
    url3 = 'http://bestiptvsrv.tk:25461/get.php?username=anis&password=anis&type=m3u'  # this link should not work
    urls = [url1, url2, url3]
    valid_requests = []
    for url in urls:
        request = requester.request(url)
        if request is not None:
            valid_requests.append(url)

    assert valid_requests == [url1, url2]


def error_check_request():
    url1 = None
    url2 = 23
    url3 = '//www.reddit.com'
    url4 = 'www.google.com'
    urls = [url1, url2, url3, url4]
    for url in urls:
        with pytest.raises(InvalidURLException):
            requester.request(url)


def test_get_format():
    request1 = requester.request('http://freedailyiptv.com/links/29-05-2018/SE_freedailyiptv.com.m3u')
    request2 = requester.request('http://freedailyiptv.com/links/11-06-2018/World_freedailyiptv.com.m3u')
    request3 = requester.request(
        'http://xsat.me:31000/get.php?username=mahmood&password=mahmood&type=m3u')  # not an m3u
    request4 = requester.request('https://dailyiptvlist.com/dl/us-m3uplaylist-2018-06-12-1.m3u')
    request5 = requester.request('https://cafe-tv.net/wp-content/uploads/2018/06/france0606.m3u')
    request6 = requester.request('https://www.colorado.edu/conflict/peace/download/peace.zip')
    request7 = requester.request('https://www.colorado.edu/conflict/peace/download/peace_treatment.ZIP')
    request8 = requester.request('http://www.mediafire.com/file/opkx06qikkxetya/IPTV-Espa%C3%B1a-M3u-Playlist-'
                                 'Update-17-12-2017.zip')
    format1 = requester.get_format(request1)
    format2 = requester.get_format(request2)
    format3 = requester.get_format(request3)
    format4 = requester.get_format(request4)
    format5 = requester.get_format(request5)
    format6 = requester.get_format(request6)
    format7 = requester.get_format(request7)
    format8 = requester.get_format(request8)
    m3us = [format1, format2, format4, format5]
    zips = [format6, format7]
    htmls = [format3, format8]
    for f in m3us:
        assert f == 'm3u', 'Error: incorrect format'
    for f in zips:
        assert f == 'zip', 'Error: incorrect format'
    for f in htmls:
        assert f == 'html', 'Error: incorrect format'


def error_check_get_format():
    request1 = None
    request2 = 23
    request3 = 'http//www.reddit.com'
    request4 = 'www.google.com'
    requests = [request1, request2, request3, request4]
    for request in requests:
        with pytest.raises(InvalidRequestException):
            requester.get_format(request)


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


def error_check_hash_content():
    file1 = None
    file2 = 23
    file3 = []
    file4 = open(r'C:\Users\pharvie\Desktop\Test Cases\America1.zip')
    for f in [file1, file2, file3, file4]:
        with pytest.raises(InvalidInputException):
            requester.hash_content(f)


def test_deport():
    url1 = requester.deport('http://192.68.132.1:800')
    url2 = requester.deport('http://132.100.12.1')
    url3 = requester.deport('http://www.fattyport:80')
    url4 = requester.deport('http://www.something:81')
    url5 = requester.deport('http://www.otherthing')
    url6 = requester.deport('http://s4.bossna-caffe.com:80/hls/1200.m3u8?channelId=1200&deviceMac='
                            '00:1A:79:3A:2D:B9&uid=35640')
    url7 = requester.deport('http://s0.balkan-x.net:80/playlist?type=m3u&deviceMac=00:1A:79:3A:2D:B9')

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
        with pytest.raises(InvalidURLException):
            requester.deport(url)


def test_prepare():
    url1 = requester.prepare('http://s4.bossna-caffe.com:80/hls/1200.m3u8?channelId=1200&deviceMac='
                             '00:1A:79:3A:2D:B9&uid=35640')
    url2 = requester.prepare('http://s0.balkan-x.net:80/playlist?type=m3u&deviceMac=00:1A:79:3A:2D:B9')
    url3 = requester.prepare('http://192.68.132.1:800')
    url4 = requester.prepare('http://www.soledge7.dogannet.tv/S1/HLS_LIVE/tv2/1000/prog_index.m3u8')
    url5 = requester.prepare('http://www.reddit.com')
    url6 = requester.prepare('http://www.s4.bossna-caffe.com:40/hls/1200.m3u8?channelId=1200&deviceMac='
                             '00:1A:79:3A:2D:B9&uid=35640')
    url7 = requester.prepare('http://www.s0.balkan-x.net:40/playlist?type=m3u&deviceMac=00:1A:79:3A:2D:B9')

    assert url1 == url6 == 'http://s4.bossna-caffe.com'
    assert url2 == url7 == 'http://s0.balkan-x.net'
    assert url3 == 'http://192.68.132.1'
    assert url4 == 'http://soledge7.dogannet.tv'
    assert url5 == 'http://reddit.com'


def error_check_prepare():
    url1 = None
    url2 = 23
    url3 = '//www.reddit.com'
    url4 = 'www.google.com'
    urls = [url1, url2, url3, url4]
    for url in urls:
        with pytest.raises(InvalidURLException):
            requester.prepare(url)


def test_remove_top():
    domain1, top1 = requester.remove_top('http://www.reddit.com/r/all')
    domain2, top2 = requester.remove_top('http://www.ak-ahmaid.1up.next.com/anythinggoes')
    domain3, top3 = requester.remove_top('http://bit.ly/AWEr')
    domain4, top4 = requester.remove_top('https://goo.gl/x6khNK')

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
        with pytest.raises(InvalidURLException):
            requester.remove_top(url)


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


def error_check_subpaths():
    url1 = None
    url2 = 23
    url3 = []
    url4 = 'www.reddit.com'
    urls = [url1, url2, url3, url4]
    for url in urls:
        with pytest.raises(InvalidURLException):
            requester.subpaths(url)


def test_purity():
    purity1 = requester.purity(['r', 'all'])
    purity2 = requester.purity(['u', 'capshockey', 'submitted'])
    purity3 = requester.purity(['2018', '06', 'iptv-m3u-sport'])
    purity4 = requester.purity(['bqxon'])
    purity5 = requester.purity(requester.subpaths('http://www.freshiptv.com/free-cccam-servers-world-cup'))
    purity6 = requester.purity([])

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
        with pytest.raises(InvalidURLException):
            requester.remove_top(sub)


def test_params():
    url1 = 'https://www.list-iptv.com/search/label/Download%20iptv%20uk?&max-results=10'
    url2 = 'http://www.facebook.com/sharer.php?u=https://www.list-iptv.com/'
    url3 = 'https://i0.wp.com/cafe-tv.net/wp-content/uploads/2017/11/Extension-exodus-Repo-Addon-Kodi-install-3.jpg?fit=985%2C501&ssl=1'
    url4 = 'https://www.blogger.com/share-post.g?blogID=1041638923557619843&postID=3582939062652584883&target=twitter'
    url5 = 'http://kibuilder.com/RoG'
    url6 = 'http://adf.ly/HmtTG'
    url7 = 'http://rapidtory.com/1seI'
    url8 = 'http://www.reddit.com/r/all/fiteme'

    for url in [url1, url2, url3, url4]:
        assert requester.params(url) == 1

    for url in [url5, url6, url7, url8]:
        assert requester.params(url) == 0


def error_check_params():
    url1 = None
    url2 = 23
    url3 = []
    url4 = 'www.reddit.com'
    urls = [url1, url2, url3, url4]
    for url in urls:
        with pytest.raises(InvalidURLException):
            requester.params(url)


def test_phrases():
    phrases1 = requester.phrases('http://www.reddit.com/r/all')
    phrases2 = requester.phrases('http://www.freshiptv.com/free-30-iptv-list-premium-worldsport-hd-sd-channels-m3u')
    phrases3 = requester.phrases('https://www.list-iptv.com/p/telecharger-iptv-france.html')
    phrases4 = requester.phrases('http://www.reddit.com')

    assert phrases1 == 'r all'
    assert phrases2 == 'free iptv list premium worldsport hd sd channels m3u'
    assert phrases3 == 'p telecharger iptv france html'
    assert phrases4 == ''


def error_check_phrases():
    url1 = None
    url2 = 23
    url3 = []
    url4 = 'www.reddit.com'
    urls = [url1, url2, url3, url4]
    for url in urls:
        with pytest.raises(InvalidURLException):
            requester.phrases(url)


#my_fixer method method
#checks the return of the partial method
def test_partial():
    host = 'https://www.reddit.com'
    url1 = fixer.partial('//www.reddit.com', host)
    url2 = fixer.partial('/r/aww/top', host)
    url3 = fixer.partial('https://www.reddit.com/r/aww', host)
    url4 = fixer.partial('//www.facebook.com', host)
    url5 = fixer.partial('/r/MemeEconomy/comments/8or7ar/i_see_limited_potential_but_possible_useful/', host)
    url6 = fixer.partial('//reddit.com/r/all', host)
    url7 = fixer.partial('http://reddit.com/r/all', host)
    assert url1 == 'https://www.reddit.com'
    assert url2 == 'https://www.reddit.com/r/aww/top'
    assert url3 == 'https://www.reddit.com/r/aww'
    assert url4 == 'https://www.facebook.com'
    assert url5 == 'https://www.reddit.com/r/MemeEconomy/comments/8or7ar/i_see_limited_potential_but_possible_useful/'
    assert url6 == 'https://reddit.com/r/all'
    assert url7 == 'http://reddit.com/r/all'


#my_fixer method
#error checks the partial method
def error_check_partial():
    host = 'https://www.reddit.com'
    url1 = None
    url2 = 23
    url3 = []
    urls = [url1, url2, url3]
    for url in urls:
        with pytest.raises(InvalidInputException):
            fixer.partial(url, host)
    for url in urls:
        with pytest.raises(InvalidHostException):
            fixer.partial(host, url)


#my_fixer method
#checks the return of the phish method
def test_phish():
    url1 = fixer.phish('http://198.255.114.218:8000/get.php?username=j9&password;=j9&type;=m3u')
    url2 = fixer.phish('http://iptv.alkaicerteams.com:8080/get.php?username=alkaicer_66m62772&password;='
                           '3bjwn4c6&type;=m3u')
    url3 = fixer.phish('http://www.reddit.com/abc;def')
    url4 = fixer.phish('http://iptvurllist.com/upload/file/2016-03-27IPTV Italy Channels url Links.m3u')
    assert url1 == 'http://198.255.114.218:8000/get.php?username=j9&password=j9&type=m3u'
    assert url2 == 'http://iptv.alkaicerteams.com:8080/get.php?username=alkaicer_66m62772&password=3bjwn4c6&type=m3u'
    assert url3 == 'http://www.reddit.com/abc;def'
    assert url4 == 'http://iptvurllist.com/upload/file/2016-03-27IPTV%20Italy%20Channels%20url%20Links.m3u'


#my_fixer method
#error checks the phish method
def error_check_phish():
    url1 = None
    url2 = 23
    urls = [url1, url2]
    for url in urls:
        with pytest.raises(InvalidInputException):
            fixer.phish(url)


#my_fixer method
#checks the return of the expand method
def test_expand():
    url1 = fixer.expand('https://www.reddit.com')
    url2 = fixer.expand('https://bit.ly/1f3xnd9')  # https://www.reddit.com/r/all
    url3 = fixer.expand('https://bitly.com/')
    url4 = fixer.expand('https://bit.ly/188dxN0')  # https://www.facebook.com
    url5 = fixer.expand('https://ift.tt/2GnlsZS')
    url6 = fixer.expand('https://goo.gl/Nc38rb')
    assert url1 == 'https://www.reddit.com'
    assert re.search(r'https:\/\/www.reddit.com\/r\/all\/?', url2) is not None
    assert url3 == 'https://bitly.com/'
    assert url4 == 'https://www.facebook.com/'
    assert url5 == 'http://163.172.51.84:25461/live/superiptv1/superiptv111/21523.ts'
    assert requester.host(url6) == 'https://doc-10-50-docs.googleusercontent.com'


#my_fixer method
#error checks the expand method
def error_check_expand():
    url1 = None
    url2 = 23
    url3 = '//www.reddit.com'
    url4 = 'www.google.com'
    urls = [url1, url2, url3, url4]
    for url in urls:
        with pytest.raises(InvalidURLException):
            fixer.expand(url)


#my fixer_method
#checks the return of the reduce method
def test_reduce():
    url1 = fixer.reduce('http://reddit.com/')
    url2 = fixer.reduce('http://reddit.com')

    assert url1 == url2

#my_fixer method
#error checks the reduce method
def error_check_reduce():
    url1 = None
    url2 = 23
    url3 = '//www.reddit.com'
    url4 = 'www.google.com'
    urls = [url1, url2, url3, url4]
    for url in urls:
        with pytest.raises(InvalidURLException):
            fixer.reduce(url)


#node method
#error checks the initialization of the node class
def error_check_init_node():
    parent1 = 1
    parent2 = []
    parent3 = set()
    parent4 = 'string'
    for parent in [parent1, parent2, parent3, parent4]:
        with pytest.raises(InvalidInputException):
            node = Node('Anything', parent)


#node method
#checks the return of the data method
def test_data():
    node1 = Node('fat cat', None)
    node2 = Node([1, 2, 3], node1)
    node3 = Node('Anything goes', None)
    node4 = Node(4, None)
    node5 = Node(set(), None)

    assert node1.data() == 'fat cat'
    assert node2.data() == [1, 2, 3]
    assert node3.data() == 'Anything goes'
    assert node4.data() == 4
    assert node5.data() == set()


#node method
#checks the set_data method works properly
def test_set_data():
    node1 = Node('fat cat', None)
    node1.set_data('not fat')

    assert node1.data() == 'not fat'

    node1.set_data('fat')
    node2 = Node(node1.data(), None)

    assert node1.data() == 'fat'
    assert node2.data() == 'fat'

#node method
#checks the return of the parent method
def test_parent():
    node1 = Node(1, None)
    node2 = Node(2, node1)
    node3 = Node(3, node1)
    node4 = Node(4, node2)
    node5 = Node(5, node3)

    assert node2.parent() == node3.parent() == node1
    assert node4.parent() == node2
    assert node5.parent() == node3
    assert node4.parent().parent() == node5.parent().parent() == node1

#node method
#checks the return of the children method
def test_children():
    node1 = Node(1, None)
    node2 = node1.add_child(2)
    node3 = node1.add_child(3)
    node4 = node2.add_child(4)
    node5 = node3.add_child(5)
    node6 = node2.add_child(6)

    assert node1.children() == [node2, node3]
    assert node2.children() == [node4, node6]
    assert node3.children() == [node5]


def test_has_children():
    node1 = Node(1, None)
    node2 = node1.add_child(2)
    node3 = node1.add_child(3)
    node4 = node2.add_child(4)
    node5 = node3.add_child(5)
    node6 = node2.add_child(6)

    for node in [node1, node2, node3, node4.parent(), node5.parent(), node6.parent()]:
        assert node.has_children() is True

    for node in [node4, node5, node6]:
        assert node.has_children() is False

#node method
#checks the return of the has parent method
def test_has_parent():
    node1 = Node(1, None)
    node2 = node1.add_child(2)
    node3 = node1.add_child(3)
    node4 = node2.add_child(4)
    node5 = node3.add_child(5)
    node6 = node2.add_child(6)

    for node in [node2, node3, node4, node5, node6]:
        assert node.has_parent() is True

    for node in [node1, node2.parent(), node3.parent(), node4.parent().parent()]:
        assert node.has_parent() is False


#node method
#checks the return of the parents method
def test_parents():
    node1 = Node(1, None)
    node2 = node1.add_child(2)
    node3 = node1.add_child(3)
    node4 = node2.add_child(4)
    node5 = node3.add_child(5)
    node6 = node2.add_child(6)

    assert node1.parents() == []
    assert node2.parents() == node3. parents() == [node1]
    assert node4.parents() == node6.parents() == [node2, node1]
    assert node5.parents() == [node3, node1]


#node method
#checks the return of the descendants method
def test_descendants():
    node1 = Node(1, None)
    node2 = node1.add_child(2)
    node3 = node1.add_child(3)
    node4 = node2.add_child(4)
    node5 = node3.add_child(5)
    node6 = node2.add_child(6)
    node7 = node6.add_child(7)

    assert node1.descendants() == [node2, node3, node4, node6, node5, node7]
    assert node2.descendants() == [node4, node6, node7]
    assert node3.descendants() == [node5]
    assert node6.descendants() == [node7]
    assert node4.descendants() == node5.descendants() == node7.descendants() == []


#node method
#checks the return of the siblings method
def test_siblings():
    node1 = Node(1, None)
    node2 = node1.add_child(2)
    node3 = node1.add_child(3)
    node4 = node2.add_child(4)
    node5 = node3.add_child(5)
    node6 = node2.add_child(6)
    node7 = node6.add_child(7)

    assert node1.siblings() == node5.siblings() == node7.siblings() == []
    assert node2.siblings() == [node3]
    assert node3.siblings() == [node2]
    assert node4.siblings() == [node6]
    assert node6.siblings() == [node4]


#node method
#checks the return of the depth method
def test_depth():
    node1 = Node(1, None)
    node2 = node1.add_child(2)
    node3 = node1.add_child(3)
    node4 = node2.add_child(4)
    node5 = node3.add_child(5)
    node6 = node2.add_child(6)
    node7 = node6.add_child(7)

    assert node1.depth() == 0
    assert node2.depth() == node3.depth() == 1
    assert node4.depth() == node5.depth() == node6.depth() == 2
    assert node7.depth() == 3

#Crawler method
#Error checking for the unzip method
def error_check_unzip():
    crawler = Crawler()
    request1 = None
    request2 = 23
    request3 = 'http//www.reddit.com'
    request4 = 'www.google.com'
    requests = [request1, request2, request3, request4]
    for request in requests:
        with pytest.raises(InvalidRequestException):
            crawler.unzip(request)



#Queue method
#Checks that the enqueue methods works correctly by using the size method
def test_enqueue():
    q = Queue()
    q.enqueue(1)
    q.enqueue(5)
    q.enqueue(10)

    assert q.size() == 3

    q.enqueue(5)
    q.enqueue(8)

    assert q.size() == 5


#Queue method
#Checks the dequeue methods work correctly by checking its return
def test_dequeue():
    q = Queue()
    q.enqueue(1)
    q.enqueue(2)
    q.enqueue(3)
    order = []
    while not q.empty():
        order.append(q.dequeue())

    assert order == [1, 2, 3]

    q.enqueue(1)
    q.enqueue(2)
    q.enqueue(3)
    q.enqueue(4)
    q.dequeue()
    q.dequeue()
    q.enqueue(5)
    q.enqueue(6)
    order = []

    while not q.empty():
        order.append(q.dequeue())

    assert order == [3, 4, 5, 6]


#Queue method
#Error checks the dequeue method
def error_check_dequeue():
    q = Queue()

    with pytest.raises(EmptyQueueException):
        q.dequeue()

    q.enqueue(1)
    q.dequeue()

    with pytest.raises(EmptyQueueException):
        q.dequeue()


#Queue method
#Checks the return of the peek method
def test_peek():
    q = Queue()
    q.enqueue(1)
    q.enqueue(2)
    q.enqueue(3)

    assert q.peek() == 1
    assert q.peek() == 1

    q.dequeue()

    assert q.peek() == 2

# Queue method
# Error checks the dequeue method
def error_check_peek():
        q = Queue()

        with pytest.raises(EmptyQueueException):
            q.peek()

        q.enqueue(1)
        q.dequeue()

        with pytest.raises(EmptyQueueException):
            q.peek()


#my_tester method
#A helper method that takes in a list of urls, creates a test helper for each url, and concatenates the streams found
#at each url based on the inputted method
def crawler_helper(urls, method='check'):
    streams = set()
    for url in urls:
        crawler = Crawler(test=url)
        if method is 'check':
            crawler.check(url)
        elif method is 'text':
            r = requester.request(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            splitext = crawler.check_text_urls(soup)
            crawler.parse_text(splitext, url)
        elif method is 'ref':
            r = requester.request(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            crawler.check_ref_urls(soup, url)
        elif method is 'crawl':
            crawler.crawl(url, recurse=False)
            crawler.eliminate()
        for stream in crawler.get_streams():
            streams.add(stream)
    return streams


#Crawler method
#Tests that the crawler correctly parse m3us
def test_parse_with_m3u():
    url1 = fixer.expand('https://bit.ly/2t05257')
    url2 = 'https://www.dailyiptvlist.com/dl/pt-m3uplaylist-2018-06-11.m3u'
    url3 = 'http://premium-iptv.link:6969/get.php?username=despina&password=despina&type=m3u'
    url4 = 'https://cafe-tv.net/wp-content/uploads/2017/05/italia090501.m3u'
    url5 = 'http://iptvurllist.com/upload/file/2017-07-29Iptv-France-Server-Playlist-Url-Link-m3u-29-07.m3u'
    url6 = 'https://cafe-tv.net/wp-content/uploads/2017/05/italia090501.m3u'
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
    assert 'https://adultswim-vodlive.cdn.turner.com' in streams
    assert 'http://82.192.84.30' in streams
    assert 'http://streamer-cache.grnet.gr' in streams
    assert 'http://178.62.176.153' in streams


#Crawler method
#Tests that hte crawler correctly parses m3us from download files
#NOTE: all three of these files contain streams that do not have defined extensions
def test_parse_with_download():
    url1 = 'http://173.56.74.197:9981/playlist/channels'
    url2 = 'http://125.130.197.49:9981/playlist'
    url3 = 'https://hdbox.ws/en/?wpfb_dl=17328'
    url4 = 'https://drive.google.com/uc?export=download&id=1kNL8nfRL1F0x52wYZ9uJC98aElpqIntw'
    url5 = 'https://drive.google.com/uc?export=download&id=17xs13weC42ZudxkAH_LNBeCR3R0IX_F8'
    urls = [url1, url2, url3, url4, url5]
    streams = crawler_helper(urls)

    assert 'http://173.56.74.197' in streams
    assert 'http://125.130.197.49' in streams
    assert 'http://37.235.216.4' in streams
    assert 'http://xtv.satarabia.com' in streams
    assert 'http://164.132.200.17' in streams

#Crawler method
#Tests that the crawler correctly parses m3us from zip files
def test_parse_with_zip():
    url1 = 'http://www.mediafire.com/file/opkx06qikkxetya/IPTV-Espa%C3%B1a-M3u-Playlist-Update-17-12-2017.zip'
    url2 = 'https://www.mediafire.com/file/mjvk5vrarb39q8e/IPTV-Turkish-M3u-Channels-Update-04-12-2017.zip'
    url3 = 'https://www.colorado.edu/conflict/peace/download/peace_treatment.ZIP'
    url4 = 'http://download1586.mediafire.com/zat78d8fdnkg/0dpgto94u7q74r4/IPTV-M3u-Sport-All-Channels-List-17-12-2017.zip'
    url5 = 'http://www.mediafire.com/file/bu19timjoao110c/IPTV-Espa%C3%B1a-M3u-Playlist-Update-12-12-2017.zip' #works with utf-8 is none
    url6 = 'http://www.mediafire.com/file/rrpvrj0rdgealj4/IPTV-Turk-M3u-Playlist-Update-12-12-2017.zip' #same thing
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


#Crawler method
#Tests that the crawler correctly opens m3u files it finds while parsing an m3u file
def test_parse_text_from_parse():
    url1 = 'http://www.mediafire.com/file/35txqby0vtpzvva/IPTV+World+Mix+M3u+.Update+All+Channels+21-11-2017.m3u'
    url2 = 'http://dwstream4-lh.akamaihd.net/i/dwstream4_live@131329/master.m3u8'
    url3 = 'http://theblaze.global.ssl.fastly.net/live/blaze-dvr/master.m3u8'  #also contains relatives
    urls = [url1, url2, url3]
    streams = crawler_helper(urls)

    assert 'http://wms.shared.streamshow.it' in streams
    assert 'http://37.187.142.147' in streams
    assert 'http://cremona1.econcept.it' in streams
    assert 'http://live.streamcaster.net' in streams
    assert 'http://wow01.105.net' in streams
    assert 'http://skyianywhere2-i.akamaihd.net' in streams
    assert 'http://dwstream4-lh.akamaihd.net' in streams
    assert 'http://theblaze.global.ssl.fastly.net' in streams

#Crawler method
#Tests that the crawler correctly opens relative urls found while parsing an m3u file
def test_parse_with_relatives():
    url1 = 'http://soledge7.dogannet.tv/S1/HLS_LIVE/tv2/1000/prog_index.m3u8'  # ts files only
    url2 = 'https://ucankus-live.cdnnew.com/ucankus/ucankus.m3u8'  # ts files only
    url3 = 'http://publish.thewebstream.co:1935/studio66tv/_definst_/studio66tv_channel11/playlist.m3u8'  # m3u file
    url4 = 'http://bqgsd19q.rocketcdn.com/kralpop_720/chunklist.m3u8'  # ts files only
    urls = [url1, url2, url3, url4]
    streams = crawler_helper(urls)
    
    assert 'http://soledge7.dogannet.tv' in streams
    assert 'https://ucankus-live.cdnnew.com' in streams
    assert 'http://publish.thewebstream.co' in streams
    assert 'http://bqgsd19q.rocketcdn.com' in streams

#Crawler method
#Tests the crawler correctly finds and parses m3u and ts files in the text of a web page
def test_text_urls():
    url1 = 'http://iptvurllist.com/view_article.php?id=428-Iptv-France-Server-Playlist-Url-Link-m3u-29-07.html'  #ts
    url2 = 'http://www.ramalin.com/iptv-russian-tv-channels-playlist-12-06-2018/'  # ts
    url3 = 'https://www.dailyiptvlist.com/italy-iptv-m3u-playlist-download-14-jun-2018/'  #m3us
    url4 = 'http://iptvsatlinks.blogspot.com/2018/06/russia-uk-usa-pak-m3u-bbc-itv-sky.html'  #ts
    url5 = 'http://www.ramalin.com/poland-iptv-channels-playlist-07-06-2018/'  #ts segments
    url6 = 'http://www.iptvm3u.com/2018/03/iptv-england-server-m3u-list-update-02.html' #ts
    url7 = 'http://freeworldwideiptv.com/2018/06/19/germany-smart-tv-xbmc-iptv-m3u-playlist-19-06-2018/' #ts
    urls = [url1, url2, url3, url4, url5, url6, url7]
    streams = crawler_helper(urls, 'text')

    assert 'http://62.210.245.19' in streams
    assert 'http://95.47.66.243' in streams
    assert 'http://217.182.173.184' in streams
    assert 'http://193.200.164.171' in streams
    assert 'http://vismanx1.com' in streams
    assert 'http://163.172.222.83' in streams
    assert 'http://91.123.176.105' in streams
    assert 'http://gigaiptv.tk' in streams
    assert 'http://mlsh.co'
    assert 'http://145.239.205.121' in streams


#Crawler method
#Tests that the crawler correctly finds and parses m3u files from the referenced url of a webpage
def test_ref_urls():
    url1 = 'https://cafe-tv.net/2018/06/iptv-m3u-sport-speciale-coupe-du-monde-russie-2018'
    url2 = 'https://freedailyiptv.com/usa-m3u-free-daily-iptv-list-18-06-2018'
    urls = [url1, url2]
    streams = crawler_helper(urls, 'ref')

    assert 'http://145.239.245.159' in streams
    assert 'http://185.212.111.5' in streams
    assert 'http://tv.smartal.net' in streams
    assert 'http://185.71.66.108' in streams
    assert 'http://185.2.83.231' in streams
    assert 'http://212.8.250.12' in streams
    assert 'http://mypanel.tv' in streams


def test_identical_m3us():
    crawler = Crawler()
    url1 = 'http://iptvurllist.com/view_article.php?id=82-IPTV-Italy-Channels-url-Links.html'
    url1repeat = 'http://iptvurllist.com/upload/file/2016-03-27IPTV Italy Channels url Links.m3u'
    crawler.crawl(url1, recurse=False)
    crawler.crawl(url1repeat, recurse=False)


def test_eliminate():
    url = 'https://www.list-iptv.com/'
    crawler = Crawler(limit=6000)
    crawler.crawl(url)
    crawler.eliminate()


def requester_tests():
    return [test_validate, test_host, error_check_host, test_remove_identifier, error_check_remove_identifier,
            test_request, error_check_request, test_get_format, error_check_get_format, test_hash_content,
            error_check_hash_content, test_deport, error_check_deport, test_prepare, error_check_prepare,
            test_remove_top, error_check_remove_top, test_subpaths, error_check_subpaths, test_purity,
            error_check_purity, test_phrases, error_check_phrases]


def fixer_tests():
    return [test_partial, error_check_partial, test_phish, error_check_phish, error_check_expand,
            test_reduce, error_check_reduce]


def node_tests():
    return [error_check_init_node, test_data, test_set_data, test_parent, test_children, test_has_children, test_has_parent,
            test_parents, test_descendants, test_siblings]


def queue_tests():
    return [test_enqueue, test_dequeue, error_check_dequeue, test_peek, error_check_peek]

def crawler_tests():
    return [test_internal, error_check_internal, error_check_unzip, test_parse_with_m3u, test_parse_with_download,
            test_parse_with_zip, test_parse_text_from_parse, test_parse_with_relatives, test_text_urls, test_ref_urls]


def get_tests():
    return requester_tests() + fixer_tests() + node_tests() + queue_tests() + crawler_tests()


def test_runner():
    for test in get_tests():
        test()


if __name__ == "__main__":
    print('Running tests...')
    test_runner()
    print('All tests passed!')
