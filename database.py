from exceptions import *
import requester
import url_mutator as um
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import socket


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
        self._client.drop_database(self._name) #drops the database if there is already one created with this name
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
        if document_from_url(self._db, url) is not None and not suppress_warnings: #checks if the url is already in the database
            raise UrlPresentInDatabaseError('The following url, %s has already been inserted into the %s database. '
                                     'Urls should only be inserted into visited databases once' % (url, self._name))
        data = {
            'url': url,
            'parent': parent,
            'importance': False
        }
        self._db.posts.insert_one(data) #inserts the url and node into the database in the form of a dictionary

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
        #TODO
        #fill in this method
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
        data = document_from_url(self._db, url)
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
            self._client = MongoClient(host='172.25.12.109', port=27017)
        except ServerSelectionTimeoutError:
            raise ServerNotRunningError('MongoDB is not currently running on the host server. Try connecting to the host server and '
                                        'enter at the command line "sudo service mongod restart"')
        self._db = self._client[self._name]

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
            raise InvalidUrlError('Cannot add an invalid url to streams: %s' % (str(url)))
        if not requester.validate_url(host):
            raise InvalidUrlError('Cannot add a url to streams with an invalid host: %s' % str(host))
        netloc = um.prepare(url)
        ip_address = socket.gethostbyname(um.remove_schema(netloc))
        if document_from_url(self._db, netloc) is None:
            data = {
                'url': netloc,
                'IP address': ip_address,
                'Linked by': [host]
            }
            self._db.posts.insert_one(data)
        else:
            self.update_linked_by(netloc, host)

    def update_linked_by(self, url, host):
        if not requester.validate_url(url):
            raise InvalidUrlError('Cannot update document with an invalid url: %s' % (str(url)))
        if not requester.validate_url(host):
            raise InvalidUrlError('Cannot update document with an invalid host: %s' % str(host))
        data = document_from_url(self._db, url)
        if not data:
            raise UrlNotInDatabaseError('The url, %s, is not in the database, %s' % (url, self._name))
        if host in data['Linked by']:
            raise HostInLinkedByError('The host, %s, is already in the linked by of %s' % (host, url))
        self._db.posts.update({'url': url}, {'$push': {'Linked by': host}})

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
Method: document_from_url
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
def document_from_url(database, url):
    if not requester.validate_url(url):
        raise InvalidUrlError('Url input to document_from_url must be a url, the following input is not a url: %s' % str(url))
    cursors = database.posts.find({'url': url})  # retrieves all cursors that contain the inputted url
    if cursors.count() > 1:  # count counts the number of cursor, if there are multiple cursors an error is raised
        raise MultipleUrlsInDatabaseError('There are multiple entries in the %s with the same url %s' % (database.name, url))
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

