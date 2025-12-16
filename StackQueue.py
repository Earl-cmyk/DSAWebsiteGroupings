class Node:
    def __init__(self, data):
        self.node = data
        self.left = None
        self.right = None


class Stack:
    def __init__(self):
        self.head = None
        self.length = 0

    def push(self, data):
        n = Node(data)
        n.left = self.head
        self.head = n
        self.length += 1

    def to_list(self):
        items = []
        cur = self.head
        while cur:
            items.append(cur.node)
            cur = cur.left
        return items


class Queue:
    """Linked-list based queue used only locally in some actions."""

    def __init__(self):
        self.head = None
        self.tail = None
        self.length = 0

    def enqueue(self, data):
        n = Node(data)
        if not self.head:
            self.head = n
            self.tail = n
        else:
            self.tail.right = n
            self.tail = n
        self.length += 1

    def dequeue(self):
        if self.length == 0:
            return None
        n = self.head
        self.head = self.head.right
        self.length -= 1
        return n.node