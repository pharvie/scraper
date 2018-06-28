from exceptions import InvalidInputException
from my_queue import Queue

class Node(object):
    def __init__(self, data, parent):
        if parent is not None and not isinstance(parent, Node):
            raise InvalidInputException('The parent of a node must either be none or a node itself')
        self._data = data
        self._parent = parent
        self._depth = 0
        if parent is not None:
            parent.children().append(self)
        if self.has_parent():
            self._depth = self.parent().depth() + 1
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

    def has_children(self):
        return len(self.children()) != 0

    def add_child(self, value):
        node = Node(value, self)
        return node

    def has_parent(self):
        return self.parent() is not None

    def parents(self):
        curr = self
        parents = []
        while curr.has_parent():
            parents.append(curr.parent())
            curr = curr.parent()
        return parents

    def descendants(self):
        queue = Queue()
        descendants = []
        for child in self.children():
            queue.enqueue(child)
        while not queue.empty():
            curr = queue.dequeue()
            descendants.append(curr)
            for child in curr.children():
                queue.enqueue(child)
        return descendants

    def siblings(self):
        siblings = []
        if not self.has_parent():
            return []
        for child in self.parent().children():
            if child is not self:
                siblings.append(child)
        return siblings

    def depth(self):
        return self._depth