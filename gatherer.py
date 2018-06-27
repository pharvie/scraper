import os.path
import os
from random import randint
import hashlib
import regex
import requester
import heapq

regex = regex.get()
expanded = {}

def add_to_path(path, polarity, url):
    h = hashlib.md5()
    h.update(url.encode('utf-8'))
    name = h.hexdigest()
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

def vocab(root, limit):
    urls = []
    state = ['train', 'test']
    polarity = ['pos', 'neg']
    vocabulary = {}
    heap = []
    counter = 0
    for s in state:
        for p in polarity:
            path = os.path.join(root, s, p)
            urls += iterator(path)
    for url in urls:
        for phrase in requester.phrases(url):
            if phrase not in vocabulary:
                vocabulary[phrase] = 0
            vocabulary[phrase] += 1
    for phrase in vocabulary:
        heapq.heappush(heap, (-vocabulary[phrase], phrase))

    while heap and counter < limit:
        entry = heapq.heappop(heap)
        vocab = entry[1]

    return vocab


def iterator(root):
    urls = []
    for file_name in os.listdir(root):
        path = os.path.join(root, file_name)
        with open(path, 'r') as f:
            url = f.read()
            urls.append(url)
    return urls
