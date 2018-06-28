import os.path
import os
from random import randint
import hashlib
import regex
import requester
import heapq
from exceptions import InvalidURLException

regex = regex.get()

def add_to_path(path, polarity, url, string):
    if not requester.validate(url):
        raise InvalidURLException('Training data must contain a valid url:' + str(url))
    if not os.path.exists(path):
        os.makedirs(path)
        fill(path)
    h = hashlib.md5()
    h.update(url.encode('utf-8'))
    name = h.hexdigest()
    rand = randint(1, 4)
    if rand == 1:
        print('Adding', string, 'to test', polarity, ':', name)
        path = os.path.join(path, 'test', polarity)
    else:
        print('Adding', string, 'to train', polarity, ':', name)
        path = os.path.join(path, 'train', polarity)
    complete = os.path.join(path, str(name) + '.txt')
    f = open(complete, 'w')
    try:
        f.write(string)
    except UnicodeEncodeError:
        print('Unicode error at', str(string))
    f.close()

def vocab(root, limit=float('inf')):
    urls = []
    frequency = {}
    heap = []
    vocab = ['None']
    counter = 0
    state = ['train', 'test']
    polarity = ['pos', 'neg']
    for s in state:
        for p in polarity:
            path = os.path.join(root, s, p)
            urls += iterator(path)
    for url in urls:
        for phrase in requester.phrases(url):
            if phrase not in frequency:
                frequency[phrase] = 0
            frequency[phrase] += 1
    for phrase in frequency:
        heapq.heappush(heap, (-frequency[phrase], phrase))
    while heap and counter < limit:
        counter += 1
        entry = heapq.heappop(heap)
        if -entry[0] > 1:
            vocab.append(entry[1])
        else:
            break
    return vocab


def purge(root):
    state = ['train', 'test']
    polarity = ['pos', 'neg']
    for s in state:
        for p in polarity:
            directory = os.path.join(root, s, p)
            for filename in os.listdir(directory):
                path = os.path.join(directory, filename)

def iterator(directory):
    urls = []
    for filename in os.listdir(directory):
        path = os.path.join(directory, filename)
        with open(path, 'r') as f:
            url = f.readlines()[0]
            urls.append(url)
            print(url)
            f.close()
    return urls


def fill(path):
    state = ['train', 'test']
    polarity = ['pos', 'neg']
    for s in state:
        subpath = os.path.join(path, s)
        if not os.path.exists(subpath):
            os.makedirs(subpath)
        for p in polarity:
            subpath = os.path.join(path, s, p)
            if not os.path.exists(subpath):
                os.makedirs(subpath)


purge('C:\\Users\\pharvie\\Desktop\\Training\\freshiptv')
