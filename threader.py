import threading
from crawler import Crawler
import heapq


class MyThread(threading.Thread):
    def __init__(self, page):
        threading.Thread.__init__(self)
        self.page = page
        self.ts_files = []

    def run(self):
        crawler = Crawler(train=True)
        crawler.crawl(self.page)
        evaluate_parse(crawler, self.page)
        crawler.eliminate()

    def get_ts(self):
        return self.ts


def evaluate_parse(crawler, page):
    print('FINISHED CRAWLING ' + page)
    ts = crawler.get_streams()
    heap = []
    if ts:
        for key in ts:
            heapq.heappush(heap, (-len(ts[key]), key))
    while heap:
        entry = heapq.heappop(heap)
        print(entry[1], ':', ts[entry[1]])


def create_threads():
    print('Threading...')
    thread1 = MyThread('http://www.freshiptv.com')
    thread2 = MyThread('http://iptvsatlinks.blogspot.com')
    thread3 = MyThread('https://cafe-tv.net')
    thread4 = MyThread('https://freedailyiptv.com')
    thread5 = MyThread('http://www.m3uliste.pw')
    thread6 = MyThread('https://www.list-iptv.com')
    thread7 = MyThread('http://iptvurllist.com')
    thread8 = MyThread('http://freeworldwideiptv.com') #503 status code
    thread9 = MyThread('http://ramalin.com')
    return[thread7]
    #return [thread1, thread2, thread3, thread4, thread5, thread6, thread7, thread8, thread9]

def run_threads():
    threads = create_threads()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


if __name__ == '__main__':
    run_threads()
