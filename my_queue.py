from exceptions import EmptyQueueException

class Queue(object):
    def __init__(self):
        self.s1 = []
        self.s2 = []

    def enqueue(self, item):
        self.s1.append(item)
        return item

    def dequeue(self):
        if self.empty():
            raise EmptyQueueException('Cannot dequeue from empty queue')
        if self.s2:
            return self.s2.pop()
        while self.s1:
            self.s2.append(self.s1.pop())
        return self.s2.pop()

    def size(self):
        return len(self.s1) + len(self.s2)

    def empty(self):
        return self.size() == 0

    def peek(self):
        if self.empty():
            raise EmptyQueueException('Cannot peek from empty queue')
        if self.s2:
            return self.s2[-1]
        while self.s1:
            self.s2.append(self.s1.pop())
        return self.s2[-1]
