import url_mutator as um
import threading
from crawler import Crawler
from database import HostList, TitleList
import eventlet
import time

eventlet.monkey_patch()

# lists of site that are crawled, add sites to this list if you'd like for them to be crawled
# I removed the identifiers and trailing backslashes from the sites I added, you can if you want to, however, the program
# should do automatically when adding them to the hosts database
#TODO: Add this array to the config file
hosts = ['https://cafe-tv.net', 'https://freedailyiptv.com', 'http://m3uliste.pw', 'https://list-iptv.com', 'http://freshiptv.com',
     'http://iptvurllist.com', 'http://freeworldwideiptv.com', 'http://ramalin.com', 'http://i-ptv.blogspot.com',
     'https://fluxustv.blogspot.com', 'https://www.iptvsource.com', 'https://iptvhits.blogspot.com', 'http://iptvurls.com',
     'https://iptv4sat.com', 'https://gratisiptv.com', 'https://freeiptv.online', 'https://skyiptv.online',
     'https://autoiptv.net']

#TODO: Add this array to the config file
titles = ["Fox", "Game of Thrones", "ABC", "HBO", "BBC", "A&E", "Disney", "Nickelodeon", "CNN"]

host_list = HostList() # create an instance of the host list database
title_list = TitleList() # create an instance of the title list database
#TODO: Add this value to the config file
num_of_threads = 5 # sets the number of sites that will be crawled simultaneously using multi-threading, keep this number around 4-6
#TODO: Add this value to the config file
timeout = 8 # time to run the threads for (in hours)

# multi-threader instance, spawns a crawler at the inputted start page
class MyThread(threading.Thread):
    def __init__(self, page): # takes the start page as input
        threading.Thread.__init__(self)
        self.page = page

    # runs the crawler
    def run(self):
        Crawler(start_url=self.page) # crawl from the start page
        host_list.update_running(self.page, False) # if an exception is raised or the crawler finishes, set the running status to False

# add hosts from the list of hosts to the database
def add_hosts_to_database():
    for host in hosts:
        host = um.prepare_netloc(host) # prepare the network location of the host
        if host_list.entry_from_host(host) is None: # if there is not an entry at the host
            host_list.add_to_hosts(host) # add it to the database

def add_titles_to_database():
    for title in titles:
        if title_list.entry_from_title(title) is None:
            title_list.add_to_titles(title)

# pulls down hosts from the database
def pull_down_from_database():
    sites = [] # list of sites
    while host_list.find_not_running_entry() is not None and len(sites) < num_of_threads: # while there are still sites not running
        # and the length of sites is less than the defined num_of_threads
        entry = host_list.find_not_running_entry() # retrieve a non-running entry
        host = entry['host'] # retrieve the host at the entry
        sites.append(host) #
        host_list.update_running(host, True) # update the host's status to running
    return sites

# creates threads from a list of sites
def create_threads():
    sites = pull_down_from_database()
    threads = []
    for site in sites:
        thread = MyThread(site) # create a thread at the site
        threads.append(thread) # append to it the list of threads

    return threads

# runs the threads for the inputted amount of time
def run_threads():
    add_hosts_to_database() # adds the hosts to the database
    threads = create_threads() # creates the threads
    for thread in threads:
        thread.start() # starts the threads
    start = curr_time = time.time() # gets the current time
    while curr_time <= (start + timeout * 3600): # while the process has not timed out
        for thread in threads:
            if not thread.is_alive(): # check if each thread is not alive
                thread.join() # if it's not, join it
        time.sleep(1) # sleep for a second
        curr_time = time.time() # get the current time
    for thread in threads: # once a timeout is reached
        host_list.update_running(thread.page, False) # set each the running status of the entry at each thread's page to False


if __name__ == '__main__':
    #host_list.reset_running() # uncomment this line and comment out the other lines to reset the running status of all hosts
    add_hosts_to_database()
    add_titles_to_database()
    run_threads() # runs the threads


