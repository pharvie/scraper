from exceptions import *
import requester
import url_mutator as um
import regex
import re
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import socket

regex = regex.get()

"""
Class: Visitor
Purpose: Keeps track of which urls have been visited by writing the url to a database. The url, along with its parent url, 
are added to the database
"""


class Visitor(object):
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
            self._client = MongoClient(host='172.25.12.109', port=27017)
        except ServerSelectionTimeoutError:
            raise ServerNotRunningError('MongoDB is not currently running on the host server. Try connecting to the host server and '
                                        'enter at the command line "sudo service mongod restart"')
        self._client.drop_database(self._name)  # drops the database if there is already one created with this name
        self._db = self._client[self._name]

    """
    Method: visit_url
    Purpose: Keeps track of which urls have been visited by entering them into a database, along with the node corresponding to the url
    Inputs:
        url: a url
        node: a node
        supress_warning: an optional input for testing purposes, when set to true, doesn't check_for_files if the url has already been entered
        into the database
    Returns:
        n/a
    Raises:
        InvalidUrlError: if the url is invalid
        InvalidInputError: if the node is invalid
        UrlInDataBaseException: if the url is already in the database, note that this error is raised as the same url shouldn't be entered
        into the database multiple times
    """

    def visit_url(self, url, parent, suppress_warnings=False):
        if not requester.validate_url(url):
            raise InvalidUrlError('Url input to visit_url must be a url, the following input is not a url: %s' % url)
        if parent is not None and not requester.validate_url(parent):
            raise InvalidUrlError('Parent input must be none or a url, the following input is neither: %s' % (str(parent)))
        if document_from_netloc(self._db, url) is not None and not suppress_warnings:  # checks if the url is already in the database
            raise UrlPresentInDatabaseError('The following url, %s has already been inserted into the %s database. '
                                            'Urls should only be inserted into visited databases once' % (url, self._name))
        data = {
            'url': url,
            'parent': parent,
            'importance': False
        }
        self._db.posts.insert_one(data)  # inserts the url and node into the database in the form of a dictionary

    """
    Method: modify_importance_from_url
    Purpose: mututes the value of the importance Boolean in the database
    Inputs:
        url: a url, the url whose importance is being modified
    Returns:
        n/a
    Raises:
        InvalidUrlError: if the url is invalid
        UrlNotInDatabaseError: if the url has not been visited (meaning it's not in the database)
    """

    def modify_importance_by_url(self, url):
        # TODO
        # fill in this method
        pass

    """
    Method: node_from_url
    Purpose: retrieves the parent corresponding to a url from the database, note that the parent is the link that linked to the url
    Inputs:
        url: a url, the url whose parent is being retrieved
    Returns:
        parent: url that links to inputted url
    Raises:
        InvalidUrlError: if the url is invalid
        UrlNotInDatabaseError: if the url has not been visited (meaning it's not in the database)
    """

    def parent_of_url(self, url):
        if not requester.validate_url(url):
            raise InvalidUrlError('Url input to visited must be a url, the following input is not a url: %s' % str(url))
        data = document_from_netloc(self._db, url)
        if not data:
            raise UrlNotInDatabaseError('The url, %s , is not in the database, %s' % (str(url), str(self._name)))
        return data['parent']

    """
    Method: database
    Purpose: for testing purposes
    Returns: 
        the database created when the visitor is instantiated
    """

    def database(self):
        return self._db


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

    """
    Method: add_stream
    Purpose: Creates an entry in the database and adds the network location, IP address, and an array of sites that linked to a stream 
    to the entry. When more streams are found on different sites with the same network location, the site is added to the array.
    For example, if the stream http://195.181.173.249/play/movie.ts was found on http://iptvurrlist.com, then the following entry 
    would be added to the database:
        Network location: http://195.181.173.249
        IP address: 195.181.173.249
        Linked by: [http://iptvurrlist.com]
    If the stream http://195.181.173.249/play/show13.ts was then found on http://list-iptv.com, the entry would then look like:
        Network location: http://195.181.173.249
        IP address: 195.181.173.249
        Linked by: [http://iptvurrlist.com, http://list-iptv.com]
    Inputs:
        url: the url of the stream to be added to the database
        host: the host of the url
    Returns:
        n/a
    Raises:
        InvalidUrlError: if the inputted url is not an url
    """

    def add_to_stream(self, url, host):
        if not requester.validate_url(url):
            raise InvalidUrlError('Cannot add an invalid url to streams: %s' % url)
        if not requester.validate_url(host):
            raise InvalidUrlError('Cannot add a url to streams with an invalid host: %s' % host)
        netloc = um.prepare(url)
        if netloc not in self.broken_stream_links and netloc not in self.working_stream_links: # Note that network locations are only
            # added to broken_stream_links or working_stream_links if their working link status is known. Also note that visitor classes
            # are unique to crawler classes, therefore each visitor class will only deal with one host. Therefore if a stream is
            # added to the database from a given visitor class with a known working link status, then it is no longer necessary
            # to evaluate that stream, doing so would lead to redundant requests to the database
            if netloc not in self.connection_attempts:
                self.connection_attempts[netloc] = 1
            if netloc not in self.ip_addresses: #if there isn't an IP address assigned to the network location
                try:
                    ip_address = socket.gethostbyname(um.remove_schema(netloc)) #try to fetch the IP address
                except socket.gaierror: #if this error is raised then the network location is down
                    ip_address = None #set the ip_address to None
                    print('%s is invalid due to broken IP address' % url)
                    self.broken_stream_links.add(netloc) #add it = broken_stream_links
                    doc = document_from_netloc(self._db, netloc)
                    if doc:
                        if host not in doc['Linked by']:
                            self.update_linked_by(netloc, host, doc)
                    else:
                        self.add_to_document(netloc, ip_address, host, False) #add it to the database as a non-working stream
                    self.connection_attempts[netloc] = float('inf') #set the connection attempts to infinity to prevent redundant checking
                else:
                    self.ip_addresses[netloc] = ip_address #store the IP address at the network location
            else: #if there is an IP address assigned to the network location
                ip_address = self.ip_addresses[netloc] #fetch it, prevent a redundant and expensive make_request
            if self.connection_attempts[netloc] <= self.fibs[-1]: #if the connection attempts have not exceeded the last value in fibs
                if self.connection_attempts[netloc] in self.fibs: #if the current connection attempt is a fibonacci number
                    #note that I use fibonacci numbers to 'randomize' where the algorithm checks in a given m3u file, as well as prevent
                    #an absurdly high amount of requests to the database. A simple integer count could also suffice, but the checking
                    #would note be spread out across the document
                    doc = document_from_netloc(self._db, netloc) #fetch the document at the network location
                    if doc: #if the network location exists in the database
                        if host not in doc['Linked by']:
                            self.update_linked_by(netloc, host, doc)  # append it to the array of links that point to the netloc
                        if doc['Working link'] is True: #if streams from the network location work
                            print('%s is known to be valid' % url)
                            self.working_stream_links.add(netloc) #and add the netloc to working streams, as it is known to work
                        else:
                            try:
                                evaluation = requester.evaluate_stream(url)
                            except StreamTimedOutError: #except the StreamTimedError
                                print('%s is invalid due to a timeout error' % url)
                                self.broken_stream_links.add(netloc) # add the netloc to the database as a broken stream
                                # as retrying streams that timeout will be extremely costly

                            else:
                                if evaluation: #if the stream works, and doesn't have a defined working link status until now
                                    print('%s is a valid stream after %s checks' % (url, self.connection_attempts[netloc]))
                                    self.update_working_link(netloc, True, doc) #updated the working link status of the network location
                                    self.working_stream_links.add(netloc) #add the netloc to working_stream_links
                    else: #if there isn't a document at the netloc (the netloc is not in the database)
                        try:
                            evaluation = requester.evaluate_stream(url)
                        except StreamTimedOutError:
                            print('%s is invalid due to a timeout error' % url)
                            self.add_to_document(netloc, ip_address, host, False) # add the netloc to the database as a broken stream
                            # as retrying streams that timeout will be extremely costly
                            self.broken_stream_links.add(netloc)
                        else:
                            if evaluation: #if it's a working stream
                                print('%s is a valid stream' % url)
                                self.add_to_document(netloc, ip_address, host, True) #add the netloc to the database as a working stream
                                self.working_stream_links.add(netloc) #add the netloc to working_stream_links
                            else:
                                print('%s might be an invalid stream' % url)
                                self.add_to_document(netloc, ip_address, host, None) #add the netloc to the database with an unknown
                                #stream status, as the network location has only been checked once
                self.connection_attempts[netloc] += 1 #increment the number of connection attempts made
            elif self.connection_attempts[netloc] != float('inf'): #if the connection attempts have exceeded the max value in fibs then the
                # stream is invalid, don't check for streams that have been set to infinity
                print('%s is an invalid stream' % url)
                self.update_working_link(netloc, False, document_from_netloc(self._db, netloc)) #update the working link status of the
                #netloc to False
                self.broken_stream_links.add(netloc) #add the netloc to broken_stream_links

    """
    Method: updated_linked_by
    Purpose: updates the array of hosts that link to a given network location
    Inputs:
        netloc: the network location that's being updated
        host: the host that is being added to the array
        doc: the document the network location is contained in, note that the document is given as input to prevent the 
        function from having to scan the database for the document multiple times
    Returns:
        n/a
    Raises:
        InvalidUrlError: if the host or netloc is not a valid url
        UrlNotInDataBaseError: if the inputted url is not in the database
        HostInLinkedByError: if the host is already present in the array
    """

    def update_linked_by(self, netloc, host, doc):
        if not requester.validate_url(netloc):
            raise InvalidUrlError('Cannot update document with an invalid url: %s' % netloc)
        if not requester.validate_url(host):
            raise InvalidUrlError('Cannot update document with an invalid host: %s' % host)
        if not doc:
            raise UrlNotInDatabaseError('The url, %s, is not in the database, %s' % (netloc, self._name))
        if host in doc['Linked by']:
            raise HostInLinkedByError('The host, %s, is already in the linked by of %s' % (host, netloc))
        self._db.posts.update({'Network location': netloc}, {'$push': {'Linked by': host}})  #appends the host to the array

    """
    Method: updated_working_link
    Purpose: updates the working link status of a given network location
    Inputs:
        netloc: the network location that's being updated 
        working_link: the updated status of the streams at the network location 
        doc: the document the network location is contained in, note that the document is given as input to prevent the 
        function from having to scan the database for the document multiple times
    Returns:
        n/a
    Raises:
        InvalidUrlError: if the netloc is not a valid url
        UrlNotInDataBaseError: if the inputted url is not in the database
`   """

    def update_working_link(self, netloc, working_link, doc):
        if not requester.validate_url(netloc):
            raise InvalidUrlError('Cannot update document with an invalid url: %s' % netloc)
        if not doc:
            raise UrlNotInDatabaseError('The url, %s, is not in the database, %s' % (netloc, self._name))
        self._db.posts.update({'Network location': netloc}, {'$set': {'Working link': working_link}})

    """
    Method: add_to_document
    Purpose: creates a dictionary and adds it as a document to the database
    Inputs:
        netloc: network location to be added to the database
        ip_address: IP address to be added to the database
        host: host to be added to the array of links that point to the network location
        working_link: the status of streams from the network locations
            None: if unknown (note it remains unknown until a certain amount of links have been checked)
            True: if working
            False: if not working 
    Returns:
        n/a
    Raises:
        InvalidUrlError: if the netloc or the host is not a valid url
        InvalidInputError: if the ip_address is not a valid IP address
    """

    def add_to_document(self, netloc, ip_address, host, working_link):
        print('Adding %s to database' % netloc)
        if not requester.validate_url(netloc):
            raise InvalidUrlError('Cannot update document with an invalid url: %s' % netloc)
        if not requester.validate_url(host):
            raise InvalidUrlError('Cannot update document with an invalid host: %s' % host)
        if ip_address is not None and not re.search(regex['ip'], ip_address):
            raise InvalidInputError('Cannot updated document with an invalid IP address: %s' % ip_address)
        doc = document_from_netloc(self._db, netloc) #sometimes when threads are running concurrently, this additional check is needed
        if not doc:
            data = {
                'Network location': netloc,
                'IP address': ip_address,
                'Linked by': [host],
                'Working link': working_link
            }
            self._db.posts.insert_one(data)

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
Method: document_from_netloc
Purpose: Retrieves the cursor object (a pymongo object used to traverse mongodb databases) corresponding to the inputted url
Inputs:
    database: the database used
    url: a url, the url whose cursor is being retrieved
Returns:
    pymongo cursor, an iterable object that is essentially an array of dictionaries corresponding to entries in the database OR
    None, if no cursor is found corresponding to the url
Raises:
    InvalidUrlError: if the url is invalid
    MultipleUrlsInDataBaseException: if multiple cursors are found, meaning multiple entries with the same url have been entered into
    the database
"""

def document_from_netloc(database, netloc):
    if not requester.validate_url(netloc):
        raise InvalidUrlError('Url input to document_from_netloc must be a url, the following input is not a url: %s' % netloc)
    cursors = database.posts.find({'Network location': netloc})  # retrieves all cursors that contain the inputted url
    if cursors.count() > 1:  # count counts the number of cursor, if there are multiple cursors an error is raised
        raise MultipleUrlsInDatabaseError('There are multiple entries in the %s with the same url %s' % (database.name, netloc))
    if cursors.count() == 1:
        return cursors[0]  # returns the cursor corresponding to the url
    return None  # returns None if no cursor is found


"""
Method: delete
Purpose: drops the database from the client
Inputs:
    database: the database to be dropped
Returns:
    n/a
"""

def delete(database):
    client = database.client
    client.drop_database(database.name)


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
