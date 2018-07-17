from exceptions import *
import requester
import url_mutator as um
import regex
import re
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import socket
from bson.son import SON

regex = regex.get()

"""
Class: Streamer
Purpose: Keeps track of the network locations of streams (ts, mp4, mkv, etc.) that have been found, the IP address of the network location,
and the site that led to the stream. Provides methods for analyzing common patterns within the streams found, such as shared IP addresses,
network locations with the most links pointing to them, etc.
"""


class Streamer(object):
    """
        Method: __init__
        Purpose: instantiates an instance of the visitor class
        Inputs:
            name: the name of the database which the visitor instance will write
        Returns:
            n/a
        Raises:
            InvalidInputError: if the inputted name is not a string
            ServerNotRunningError: if the server the database is stored on is not currently running
        """

    def __init__(self, name):
        if name is None or not isinstance(name, str):
            raise InvalidInputError('Cannot write to a database with an invalid name: %s' % name)
        self._name = name
        try:
            self._client = MongoClient(host='172.25.12.109', port=27017)  # creates a client to run the database at on the specified server
        except ServerSelectionTimeoutError:
            raise ServerNotRunningError('MongoDB is not currently running on the host server. Try connecting to the host server and '
                                        'enter at the command line "sudo service mongod restart"')
        self._db = self._client[self._name]  # the database running on the client
        self.broken_stream_links = set()  # keeps track of network location known to lead to invalid streams,
        # prevents redundant searching in the database
        self.working_stream_links = set() # keeps track of network location known to lead to working streams,
        # prevents redundant searching the database
        self.ip_addresses = {} # keeps track of IP address of network locations to prevent redundant requests
        self.connection_attempts = {} # keeps tracks of the connection attempts a given network location has made to check for
        # stream validity
        self.fibs = fib_to(10) # a list of fibonacci numbers, increase the input to this function and the algorithm will make
        # more attempts to check the validity of a given stream, decrease the input and the algorithm will make less attempts
        # to check the validity of a given stream. Note that it will check the inputted number minus one streams, so if the input is
        # fib_to(20), 19 streams of a given netloc would be checked before declaring it invalid

    def add_to_streams(self, url, host):
        if not requester.validate_url(url):
            raise InvalidUrlError('Cannot add an invalid url to streams: %s' % url)
        if not requester.validate_url(host):
            raise InvalidUrlError('Cannot add a url to streams with an invalid host: %s' % host)
        netloc = um.prepare_netloc(url)
        if netloc not in self.broken_stream_links and netloc not in self.working_stream_links: # Note that network locations are only
            # added to broken_stream_links or working_stream_links if their working link status is known. Also note that visitor classes
            # are unique to crawler classes, therefore each visitor class will only deal with one host. Therefore if a stream is
            # added to the database from a given visitor class with a known working link status, then it is no longer necessary
            # to evaluate that stream, doing so would lead to redundant requests to the database
            if netloc not in self.ip_addresses: #if there isn't an IP address assigned to the network location
                try:
                    ip_addresses = socket.gethostbyname_ex(um.remove_schema(netloc))[2] #fetches all IP addresses from the network location
                    self.ip_addresses[netloc] = ip_addresses
                except socket.gaierror: #if this error is raised then the network location is down
                    ip_addresses = None
            else:
                ip_addresses = self.ip_addresses[netloc]
            if ip_addresses:
                stream_statuses = {}
                for ip_address in ip_addresses:
                    if (ip_address, netloc) not in self.connection_attempts:
                        self.connection_attempts[(ip_address, netloc)] = 1
                    if self.connection_attempts[(ip_address, netloc)] in self.fibs:
                        doc = self.document_from_ip_address(ip_address)
                        try:
                            entry_from_netloc = self.entry_from_netloc(doc, netloc)
                        except InvalidInputError:
                            entry_from_netloc = None
                        if entry_from_netloc and entry_from_netloc['working_link']:
                            working_link = True
                            print('Stream status of %s is known to be %s' % (netloc, working_link))
                        elif url not in stream_statuses:
                            try:
                                stream_status = requester.evaluate_stream(url)
                            except StreamTimedOutError:
                                print('Stream status of %s is false due to a timeout error' % url)
                                stream_statuses[url] = working_link = False
                            else:
                                if stream_status:
                                    print('Working stream at %s' % url)
                                    stream_statuses[url] = working_link = True
                                elif self.connection_attempts[(ip_address, netloc)] == self.fibs[-1]:
                                    print('Broken stream at %s' % url)
                                    stream_statuses[url] = working_link = False
                                else:
                                    stream_statuses[url] = working_link = None
                        else:
                            working_link = stream_statuses[url]
                        self.add_to_database_by_ip_address(doc, ip_address, netloc, host, working_link)
                        if working_link:
                            self.working_stream_links.add(netloc)
                        elif working_link is False:
                            self.broken_stream_links.add(netloc)
                    self.connection_attempts[(ip_address, netloc)] += 1
            else:
                print('%s is an invalid stream as the network location is deprecated' % url)
                self.broken_stream_links.add(netloc)
                self.add_to_database_by_ip_address(self.document_from_ip_address(None), None, netloc, host, False)
                
    def add_to_database_by_ip_address(self, doc, ip_address, netloc, host, working_link):
        if ip_address is not None and not re.search(regex['ip'], ip_address):
            raise InvalidInputError('Cannot add to database with invalid IP address: %s' % ip_address)
        if not requester.validate_url(netloc):
            raise InvalidUrlError('Cannot add to database with an invalid url: %s' % netloc)
        if not requester.validate_url(host):
            raise InvalidUrlError('Cannot add to database with an invalid host: %s' % host)
        if not doc:
            data = {
                'ip_address': ip_address,
                'network_locations': [SON([('network_location', netloc), ('linked_by', [host]), ('working_link', working_link)])]
            }
            self._db.inventory.insert(data)
        else:
            entry_from_netloc = self.entry_from_netloc(doc, netloc)
            if not entry_from_netloc:
                subdata = SON([('network_location', netloc), ('linked_by', [host]), ('working_link', working_link)])
                self._db.inventory.update({'ip_address': ip_address}, {'$push': {'network_locations': subdata}})
            else:
                if host not in entry_from_netloc['linked_by']:
                    print('%s is not in the linked_by of %s at %s' % (host, netloc, ip_address))
                    self._db.inventory.update({'ip_address': ip_address, 'network_locations.network_location': netloc},
                                              {'$push': {'network_locations.$.linked_by': host}})
                current_working_link = entry_from_netloc['working_link']
                if working_link is not None:
                    if working_link and not current_working_link or working_link is False and current_working_link is None:
                        print('Updating the working link status of %s at %s to %s as it was previously %s' %
                              (netloc, ip_address, working_link, current_working_link))
                        self._db.inventory.update({'ip_address': ip_address, 'network_locations.network_location': netloc},
                                                  {'$set': {'network_locations.$.working_link': working_link}})

    def entry_from_netloc(self, doc, netloc):
        if doc is None:
            raise InvalidInputError('Cannot retrieve entry from netloc with null document')
        if not requester.validate_url(netloc):
            raise InvalidUrlError('Cannot retrieve entry from netloc with invalid netloc: %s' % netloc)
        efn = None
        for entry in doc['network_locations']:
            if entry['network_location'] == netloc:
                efn = entry
        return efn

    def document_from_ip_address(self, ip_address):
        if ip_address is not None and not re.search(regex['ip'], ip_address):
            raise InvalidInputError('Cannot add to database with invalid IP address: %s' % ip_address)
        cursors = self._db.inventory.find({'ip_address': ip_address})  # retrieves all cursors that contain the inputted IP address
        if cursors.count() > 1:  # count counts the number of cursor, if there are multiple cursors an error is raised
            raise MultipleMatchingIPsInDatabaseError('There are multiple entries in the %s with the same IP address: %s' % (self._name, ip_address))
        if cursors.count() == 1:
            return cursors[0]  # returns the cursor corresponding to the url
        return None  # returns None if no cursor is found


    """
       Method: database
       Purpose: returns the database associated with an instance of the streamer class
       Input:
           n/a
       Returns:
           database: a pymongo database
    """

    def database(self):
        return self._db

    """
    Method: delete
    Purpose: drops the database from the client
    """

    def delete(self):
        self._client.drop_database(self._db.name)


"""
Method: fib_to
Purpose: returns an array of fibonacci numbers up to n
Example:
    fib_to(5) -> [0, 1, 1, 2, 3]
Input:
    n, number to fib to
Returns: array of fibonacci numbers
Raises:
    InvalidInputError, if n is not an integer
"""

def fib_to(n):
    if not isinstance(n, int):
        raise InvalidInputError('Cannot fib to with a non-integer input: %s' % str(n))
    fibs = [0, 1]
    for i in range(2, n + 1):
        fibs.append(fibs[-1] + fibs[-2])
    return fibs

