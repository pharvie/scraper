import threading
from crawler import Crawler


class MyThread(threading.Thread):
    def __init__(self, page, override_start_url_check=False):
        threading.Thread.__init__(self)
        self.page = page
        self.override = override_start_url_check

    def run(self):
        Crawler(start=self.page, override_start_url_check=self.override, limit=12000)
        print('Finished crawling %s' % self.page)

def create_threads():
    print('Threading...')
    thread1 = MyThread('http://freshiptv.com')
    thread2 = MyThread('http://iptvsatlinks.blogspot.com')
    thread3 = MyThread('https://cafe-tv.net')
    thread4 = MyThread('https://freedailyiptv.com')
    thread5 = MyThread('http://www.m3uliste.pw')
    thread6 = MyThread('https://www.list-iptv.com')
    thread7 = MyThread('http://iptvurllist.com')
    thread8 = MyThread('http://freeworldwideiptv.com') #503 status code
    thread9 = MyThread('http://ramalin.com')
    thread10 = MyThread('http://i-ptv.blogspot.com')
    thread11 = MyThread('https://pastebin.com/raw/M4q7YxPW', override_start_url_check=True)
    return[thread10]

def run_threads():
    threads = create_threads()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


if __name__ == '__main__':
    run_threads()


