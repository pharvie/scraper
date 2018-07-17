import threading
from crawler import Crawler


class MyThread(threading.Thread):
    def __init__(self, page, override_start_url_check=False, overridden_host=None):
        threading.Thread.__init__(self)
        self.page = page
        self.override_start_url_check = override_start_url_check
        self.overridden_host = overridden_host

    def run(self):
        Crawler(start=self.page, override_start_url_check=self.override_start_url_check, overridden_host=self.overridden_host)
        print('Finished crawling %s' % self.page)

def create_threads():
    print('Threading...')
    thread1 = MyThread('http://freshiptv.com')
    thread2 = None
    thread3 = MyThread('https://cafe-tv.net')
    thread4 = MyThread('https://freedailyiptv.com')
    thread5 = MyThread('http://www.m3uliste.pw')
    thread6 = MyThread('https://www.list-iptv.com')
    thread7 = MyThread('http://iptvurllist.com')
    thread8 = MyThread('http://freeworldwideiptv.com') #503 status code
    thread9 = MyThread('http://ramalin.com')
    thread10 = MyThread('http://i-ptv.blogspot.com')
    thread11 = MyThread('https://pastebin.com/raw/M4q7YxPW', override_start_url_check=True, overridden_host='https://fluxustv.blogspot.com')
    thread12 = MyThread('https://www.iptvsource.com')
    thread13 = MyThread('https://iptvhits.blogspot.com')
    thread14 = MyThread('http://www.iptvurls.com')
    thread15 = MyThread('https://www.iptv4sat.com')
    thread16 = MyThread('https://www.gratisiptv.com')
    thread17 = MyThread('https://freeiptv.online')
    thread18 = MyThread('https://skyiptv.online')
    thread19 = MyThread('https://autoiptv.net')
    return[thread4]

def run_threads():
    threads = create_threads()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


if __name__ == '__main__':
    run_threads()


