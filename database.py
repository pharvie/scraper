from exceptions import (InvalidInputError, InvalidUrlError, UrlNotInDatabaseError, MultipleUrlsInDatabaseError,
                        UrlInDatabaseError, ServerNotRunningError)
import requester
from node import Node
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import jsonpickle


class Visitor(object):
    """
    Method: __init__
    Purpose: instantiates an instance of the visitor class
    Inputs:
        name: the name of the database which the visitor instance will write
    Returns:
        n/a
    Raises
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
        self._client.drop_database(self._name)
        self._db = self._client[self._name]
        self._counter = 0

    """
    Method: visit_url
    Purpose: Keeps track of which urls have been visited by entering them into a database, along with the node corresponding to the url
    Inputs:
        url: a url
        node: a node
        supress_warning: an optional input for testing purposes, when set to true, doesn't check if the url has already been entered
        into the database
    Returns:
        n/a
    Raises:
        InvalidUrlError: if the url is invalid
        InvalidInputError: if the node is invalid
        UrlInDataBaseException: if the url is already in the database, note that this error is raised as the same url shouldn't be entered
        into the database multiple times
    """
    def visit_url(self, url, node, suppress_warnings=False):
        if not requester.validate(url):
            raise InvalidUrlError('Url input to visit_url must be a url, the following input is not a url: %s' % url)
        if node is None or not isinstance(node, Node):
            raise InvalidInputError('Node input to visit_url must be a Node, the following input is not a node: %s' % (str(node)))
        if self.visited(url) and not suppress_warnings: #checks if the url is already in the database (only if supress_warning is false)
            raise UrlInDatabaseError('The following url, %s , has already been inserted into the  %s database. Urls should'
                                         'only be inserted into visited databases once' % (url, self._name))
        encoded_node = jsonpickle.encode(node) #encodes the node into a format readable by the database
        data = {
            'url': url,
            'node': encoded_node,
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


    """
    Method: node_from_url
    Purpose: retrieves the node corresponding to a url from the database
    Inputs:
        url: a url, the url whose node is being retrieved
    Returns:
        the Node associated with the url
    Raises:
        InvalidUrlError: if the url is invalid
        UrlNotInDatabaseError: if the url has not been visited (meaning it's not in the database)
    """
    def node_from_url(self, url):
        if not requester.validate(url):
            raise InvalidUrlError('Url input to visited must be a url, the following input is not a url: %s' % str(url))
        data = self.document_from_url(url)
        if not data:
            raise UrlNotInDatabaseError('The url, %s , is not in the database, %s' % (str(url), str(self._name)))
        return jsonpickle.decode(data['node'])

    """
    Method: visited
    Purpose: Checks if a url is in the database
    Inputs:
        url: a url, the url whose visited status is being checked
    Returns:
        True, if the url is in the database
        False, otherwise
    Raises:
        InvalidUrlError: if the url is invalid
    """
    def visited(self, url):
        if not requester.validate(url):
            raise InvalidUrlError('Url input to visited must be a url, the following input is not a url: %s' % str(url))
        return self.document_from_url(url) is not None

    """
    Method: document_from_url
    Purpose: Retrieves the cursor object (a pymongo object used to traverse mongodb databases) corresponding to the inputted url
    Inputs:
        url: a url, the url whose cursor is being retrieved
    Returns:
        pymongo cursor, an iterable object that is essentially an array of dictionaries corresponding to entries in the database OR
        None, if no cursor is found corresponding to the url
    Raises:
        InvalidUrlError: if the url is invalid
        MultipleUrlsInDataBaseException: if multiple cursors are found, meaning multiple entries with the same url have been entered into
        the database
    """
    def document_from_url(self, url):
        if not requester.validate(url):
            raise InvalidUrlError('Url input to document_from_url must be a url, the following input is not a url: %s' % str(url))
        cursors = self._db.posts.find({'url': url}) #retrieves all cursors that contain the inputted url
        if cursors.count() > 1: #count counts the number of cursor, if there are multiple cursors an error is raised
            raise MultipleUrlsInDatabaseError('There are multiple entries in the %s with the same url %s' % (self._name, url))
        if cursors.count() == 1:
            return cursors[0] #returns the cursor corresponding to the url
        return None #returns None if no cursor is found

    """
    Method: database
    Purpose: for testing purposes
    Returns: 
        the database created when the visitor is instantiated
    """
    def database(self):
        return self._db

    """
    Method: delete
    Purpose: drops the database from the client
    Returns:
        n/a
    """
    def delete(self):
        self._client.drop_database(self._name)

