import os.path
import os
import requester
from urllib.parse import urlparse
from random import randint
import hashlib
import re
import regex
import heapq

regex = regex.get()
expanded = {}

def assign(url):
    h = hashlib.md5()
    h.update(url.encode('utf-8'))
    name = h.hexdigest()
    ud, utop = requester.remove_top(requester.remove_identifier(urlparse(url).netloc))
    if ud in expanded:
        if expanded[ud]:
            add_to_path('pos', name, url)
        else:
            add_to_path('neg', name, url)
    else:
        r = requester.request(url)
        if r:
            rd, rtop = requester.remove_top(requester.remove_identifier(urlparse(r.url).netloc))
            if ud != rd and not re.search(regex['ignore'], ud):
                print('Pre:', ud)
                print('Post:', rd)
                add_to_path('pos', name, url)
                expanded[ud] = True
            else:
                add_to_path('neg', name, url)
                expanded[ud] = False

def add_to_path(polarity, name, url):
    path = 'C:\\Users\\pharvie\\Desktop\\BitLearner'
    rand = randint(1, 4)
    if rand == 1:
        print('Adding', url, 'to test', polarity, ':', name)
        path = os.path.join(path, 'test', polarity)
    else:
        print('Adding', url, 'to train', polarity, ':', name)
        path = os.path.join(path, 'train', polarity)
    complete = os.path.join(path, str(name) + '.txt')
    f = open(complete, 'w')
    try:
        f.write(url)
    except UnicodeEncodeError:
        print('Unicode error at', str(url))
    f.close()


def print_directory(directory):
    hosts = {}
    print(directory)
    for filename in os.listdir(directory):
        try:
            f = open(os.path.join(directory, filename), 'r')
        except TypeError:
            pass
        else:
            url = f.read()
            if not requester.validate(url):
                f.close()
                print('No url at', filename)
                os.unlink(os.path.join(directory, filename))
            else:
                host = requester.host(url)
                if host not in hosts:
                    hosts[host] = 0
                hosts[host] += 1

    for filename in os.listdir(directory):
        try:
            f = open(os.path.join(directory, filename), 'r')
        except TypeError:
            pass
        else:
            url = f.read()
            if not requester.validate(url):
                f.close()
                print('No url at', filename)
                os.unlink(os.path.join(directory, filename))
            else:
                host = requester.host(url)
                if hosts[host] > 100:
                    f.close()
                    os.unlink(os.path.join(directory, filename))
                    hosts[host] -= 1
    heap = []
    for host in hosts:
        heapq.heappush(heap, (-hosts[host], host))

    while heap:
        entry = heapq.heappop(heap)
        print(entry[1], ':', -entry[0])


#print_directory('C:\\Users\\pharvie\\Desktop\\BitLearner\\train\\neg')
#print_directory('C:\\Users\\pharvie\\Desktop\\BitLearner\\test\\neg')