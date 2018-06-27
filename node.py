from exceptions import InvalidInputException


class Node(object):
    def __init__(self, data, parent):
        if parent is not None and not isinstance(parent, Node):
            raise InvalidInputException('The parent of a node must either be none or a node itself')
        self._data = data
        self._parent = parent
        if parent is not None:
            parent.children().append(self)
        self._children = []

    def data(self):
        return self._data

    def set_data(self, data):
        self._data = data
        return self._data

    def parent(self):
        return self._parent

    def children(self):
        return self._children

    def add_child(self, value):
        node = Node(value, self)
        return node
