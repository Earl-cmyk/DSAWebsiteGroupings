import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def create_admin_user(db_path='feed.db'):
    """Create an admin user if one doesn't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if admin exists
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    admin = cursor.fetchone()
    
    if not admin:
        # Create admin user
        password_hash = generate_password_hash('admin123')  # In production, use a strong password
        cursor.execute(
            """
            INSERT INTO users (username, email, password, created_at)
            VALUES (?, ?, ?, datetime('now'))
            """,
            ('admin', 'admin@example.com', password_hash)
        )
        admin_id = cursor.lastrowid
        conn.commit()
        print(f"Created admin user with ID: {admin_id}")
    else:
        admin_id = admin[0]
        print(f"Admin user already exists with ID: {admin_id}")
    
    conn.close()
    return admin_id

def create_posts(admin_id, db_path='feed.db'):
    """Create educational posts with upvote/downvote functionality."""
    posts = [
        {
            'title': 'Queue',
            'caption': """
# Queue Data Structure Using Nodes in Python

## Introduction to Queue

A **Queue** is a **linear data structure** that follows the principle:

**FIFO – First In, First Out**

The first element added to the queue is the first element removed.

Queues are commonly used in:

* People lining up for services
* Printer job scheduling
* CPU task scheduling

---

## Basic Queue Operations

A queue supports the following operations:

* **Enqueue**: Insert an element at the rear of the queue
* **Dequeue**: Remove an element from the front of the queue
* **Peek / Front**: View the front element without removing it
* **isEmpty**: Check whether the queue is empty

---

## Why Implement Queue Using Nodes

In this lesson:

* Python lists are not used
* `collections.deque` is not used
* All behavior is implemented manually

Using nodes helps in understanding how queues work at a low level and how memory is linked together dynamically.

---

## Node Structure

A node is the basic unit of a queue.

Each node contains:

* Data
* A reference to the next node

```python
class Node:
    def __init__(self, data):
        self.data = data
        self.next = None
```

---

## Queue Using Linked Nodes

A queue implemented with nodes maintains two references:

* `front` points to the first element
* `rear` points to the last element

```python
class Queue:
    def __init__(self):
        self.front = None
        self.rear = None
```

---

## Enqueue Operation

The enqueue operation inserts an element at the rear of the queue.

Process:

* Create a new node
* If the queue is empty, set both front and rear to the new node
* Otherwise, attach the new node after rear and move rear

```python
    def enqueue(self, data):
        new_node = Node(data)

        if self.rear is None:
            self.front = self.rear = new_node
            return

        self.rear.next = new_node
        self.rear = new_node
```

---

## Dequeue Operation

The dequeue operation removes the front element.

Process:

* If the queue is empty, no deletion is possible
* Move front to the next node
* If the queue becomes empty, set rear to None

```python
    def dequeue(self):
        if self.front is None:
            print("Queue is empty")
            return None

        temp = self.front
        self.front = self.front.next

        if self.front is None:
            self.rear = None

        return temp.data
```

---

## Peek Operation

The peek operation returns the front element without removing it.

```python
    def peek(self):
        if self.front is None:
            return None
        return self.front.data
```

---

## Displaying Queue Elements

```python
    def display(self):
        current = self.front
        while current:
            print(current.data, end=" -> ")
            current = current.next
        print("None")
```

---

## Example Usage of Queue

```python
q = Queue()

q.enqueue(10)
q.enqueue(20)
q.enqueue(30)

q.display()

print(q.dequeue())
print(q.peek())

q.display()
```

---

# Circular Queue Using Nodes

## Circular Queue Concept

A **Circular Queue** is a variation of the queue where the last node points back to the first node instead of pointing to None.

This structure avoids unused space and allows continuous reuse of memory.

---

## Circular Queue Properties

* Front points to the first node
* Rear points to the last node
* Rear always links back to front

---

## Circular Queue Implementation

The same Node class is reused.

```python
class CircularQueue:
    def __init__(self):
        self.front = None
        self.rear = None
```

---

## Enqueue in Circular Queue

Process:

* Create a new node
* If empty, set front and rear to the node and link rear to front
* Otherwise, attach the node at rear and update the circular link

```python
    def enqueue(self, data):
        new_node = Node(data)

        if self.front is None:
            self.front = self.rear = new_node
            self.rear.next = self.front
            return

        self.rear.next = new_node
        self.rear = new_node
        self.rear.next = self.front
```

---

## Dequeue in Circular Queue

Process:

* If empty, deletion is not possible
* If only one node exists, reset front and rear
* Otherwise, move front and update rear link

```python
    def dequeue(self):
        if self.front is None:
            print("Circular Queue is empty")
            return None

        if self.front == self.rear:
            data = self.front.data
            self.front = self.rear = None
            return data

        data = self.front.data
        self.front = self.front.next
        self.rear.next = self.front
        return data
```

---

## Display Circular Queue

```python
    def display(self):
        if self.front is None:
            print("Empty")
            return

        current = self.front
        while True:
            print(current.data, end=" -> ")
            current = current.next
            if current == self.front:
                break
        print("(back to front)")
```

---

## Example Usage of Circular Queue

```python
cq = CircularQueue()

cq.enqueue(1)
cq.enqueue(2)
cq.enqueue(3)

cq.display()

print(cq.dequeue())

cq.display()
```

---

## Summary

* A queue follows the FIFO principle
* Nodes are used instead of built-in structures
* Front and rear pointers manage insertion and deletion
* A circular queue connects the rear back to the front
* Circular queues improve memory utilization

```
            """,
            'post_type': 'educational'
        },
        {
            'title': 'Stack',
            'caption': """
# Stack Data Structure Using Nodes in Python

## Introduction to Stack

A **Stack** is a **linear data structure** that follows the principle:

**LIFO – Last In, First Out**

The last element added to the stack is the first element removed.

Stacks are commonly used in:

* Undo and redo operations
* Function call management (call stack)
* Expression evaluation
* Backtracking algorithms

---

## Basic Stack Operations

A stack supports the following operations:

* **Push**: Insert an element at the top of the stack
* **Pop**: Remove the top element of the stack
* **Peek / Top**: View the top element without removing it
* **isEmpty**: Check whether the stack is empty

---

## Why Implement Stack Using Nodes

In this lesson:

* Python lists are not used
* No built-in stack utilities are used
* The stack is built manually using nodes

Using nodes helps visualize how memory is linked dynamically and how stacks work internally.

---

## Node Structure

A node is the basic unit of the stack.

Each node contains:

* Data
* A reference to the next node

```python
class Node:
    def __init__(self, data):
        self.data = data
        self.next = None
```

---

## Stack Using Linked Nodes

A stack implemented with nodes maintains only one reference:

* `top` points to the top element of the stack

```python
class Stack:
    def __init__(self):
        self.top = None
```

---

## Push Operation

The push operation inserts an element at the top of the stack.

Process:

* Create a new node
* Make the new node point to the current top
* Update top to the new node

```python
    def push(self, data):
        new_node = Node(data)
        new_node.next = self.top
        self.top = new_node
```

---

## Pop Operation

The pop operation removes the top element of the stack.

Process:

* If the stack is empty, no deletion is possible
* Store the top node
* Move top to the next node

```python
    def pop(self):
        if self.top is None:
            print("Stack is empty")
            return None

        temp = self.top
        self.top = self.top.next
        return temp.data
```

---

## Peek Operation

The peek operation returns the top element without removing it.

```python
    def peek(self):
        if self.top is None:
            return None
        return self.top.data
```

---

## Displaying Stack Elements

```python
    def display(self):
        current = self.top
        while current:
            print(current.data)
            current = current.next
```

---

## Example Usage of Stack

```python
s = Stack()

s.push(10)
s.push(20)
s.push(30)

s.display()

print(s.pop())
print(s.peek())

s.display()
```

---

## Stack Behavior Visualization

When pushing elements:

Top
30
20
10

When popping:

Top
20
10

---

## Advantages of Stack Using Nodes

* Dynamic size
* No wasted memory
* Efficient insertion and deletion

---

## Disadvantages of Stack Using Nodes

* Extra memory for pointers
* No direct access to middle elements

---

## Summary

* Stack follows the LIFO principle
* Implemented manually using linked nodes
* Push and pop operations occur at the top
* No built-in Python data structures were used

            """,
            'post_type': 'educational'
        },
        {
            'title': 'Trees in Computer Science',
            'caption': """
A Tree is a hierarchical data structure consisting of nodes connected by edges. Each node contains a value and references to its children nodes.

### Key Concepts:
- **Root**: The topmost node
- **Parent/Child**: Nodes connected by edges
- **Leaf**: Node without children
- **Height**: Length of the longest path to a leaf
- **Depth**: Length of path to the root

### Types of Trees:
1. Binary Tree
2. Binary Search Tree (BST)
3. AVL Tree
4. Red-Black Tree
5. N-ary Tree

### Example (Binary Tree in Python):
```python
class TreeNode:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None

# Create a simple tree
root = TreeNode(1)
root.left = TreeNode(2)
root.right = TreeNode(3)
```
            """,
            'post_type': 'educational'
        },
        {
            'title': 'Binary Search Trees (BST) ',
            'caption': """
A Binary Search Tree is a node-based binary tree where each node has at most two children, and for each node:
- All elements in the left subtree are less than the node's value
- All elements in the right subtree are greater than the node's value

### Key Operations:
- **Search**: O(log n) average, O(n) worst case
- **Insertion**: O(log n) average, O(n) worst case
- **Deletion**: O(log n) average, O(n) worst case
- **In-order Traversal**: Returns nodes in sorted order

### Example (BST in Python):
```python
class BSTNode:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None

def insert(root, value):
    if root is None:
        return BSTNode(value)
    if value < root.value:
        root.left = insert(root.left, value)
    else:
        root.right = insert(root.right, value)
    return root
```
            """,
            'post_type': 'educational'
        },
        {
            'title': 'Tree Traversal Algorithms',
            'caption': """
Tree traversal refers to the process of visiting each node in a tree data structure exactly once in a specific order.

### Depth-First Traversals:
1. **In-order (Left-Root-Right)**
   - Traverse left subtree
   - Visit root
   - Traverse right subtree

2. **Pre-order (Root-Left-Right)**
   - Visit root
   - Traverse left subtree
   - Traverse right subtree

3. **Post-order (Left-Right-Root)**
   - Traverse left subtree
   - Traverse right subtree
   - Visit root

### Breadth-First Traversal (Level Order):
- Visit nodes level by level, from left to right

### Example (Python):
```python
def in_order(node):
    if node:
        in_order(node.left)
        print(node.value)
        in_order(node.right)

def level_order(root):
    from collections import deque
    if not root:
        return
    queue = deque([root])
    while queue:
        node = queue.popleft()
        print(node.value)
        if node.left:
            queue.append(node.left)
        if node.right:
            queue.append(node.right)
```
            """,
            'post_type': 'educational'
        },
        {
            'title': 'List Comprehensions in Python',
            'caption': """
List comprehensions provide a concise way to create lists in Python.

### Basic Syntax:
```python
new_list = [expression for item in iterable]
```

### Examples:
```python
# Squares of numbers 0-9
squares = [x**2 for x in range(10)]

# Filter even numbers
evens = [x for x in range(10) if x % 2 == 0]

# Nested loops
pairs = [(x, y) for x in [1,2,3] for y in [3,1,4] if x != y]

# String manipulation
words = ['hello', 'world', 'python']
title_words = [word.title() for word in words]
```

### Benefits:
- More readable than traditional loops
- Often more performant than equivalent loops
- Functional programming style

### When to Use:
- Simple transformations and filtering
- Readability is improved
- Performance is critical
            """,
            'post_type': 'code_example'
        },
        {
            'title': 'Object-Oriented Programming',
            'caption': """
## 1. Encapsulation
Bundling of data with the methods that operate on that data.

```python
class BankAccount:
    def __init__(self):
        self.__balance = 0  # Private attribute
    
    def deposit(self, amount):
        if amount > 0:
            self.__balance += amount
    
    def get_balance(self):
        return self.__balance
```

## 2. Inheritance
Creating new classes from existing ones.

```python
class Animal:
    def speak(self):
        pass

class Dog(Animal):
    def speak(self):
        return "Woof!"
```

## 3. Polymorphism
Using a single interface to represent different underlying forms.

```python
def animal_sound(animal):
    print(animal.speak())

animals = [Dog(), Cat()]
for animal in animals:
    animal_sound(animal)
```

## 4. Abstraction
Hiding complex implementation details.

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self):
        pass

class Rectangle(Shape):
    def __init__(self, width, height):
        self.width = width
        self.height = height
    
    def area(self):
        return self.width * self.height
```
            """,
            'post_type': 'educational'
        },
        {
            'title': 'File Handling in Python',
            'caption': """
Python provides built-in functions for file operations.

### Reading Files:
```python
# Read entire file
with open('file.txt', 'r') as file:
    content = file.read()

# Read line by line
with open('file.txt', 'r') as file:
    for line in file:
        print(line.strip())

# Read all lines into a list
with open('file.txt', 'r') as file:
    lines = file.readlines()
```

### Writing to Files:
```python
# Write to file (overwrites)
with open('output.txt', 'w') as file:
    file.write('Hello, World!')

# Append to file
with open('output.txt', 'a') as file:
    file.write('\nNew line')
```

### File Modes:
- 'r': Read (default)
- 'w': Write (truncate)
- 'a': Append
- 'b': Binary mode
- '+': Read and write

### Best Practices:
1. Always use `with` statement
2. Handle exceptions
3. Close files properly
4. Use appropriate file modes
            """,
            'post_type': 'code_example'
        },
        {
            'title': 'Exception Handling ',
            'caption': """
Exception handling allows you to handle errors gracefully.

### Basic Try-Except:
```python
try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"Error: {e}")
```

### Multiple Exceptions:
```python
try:
    # Code that might raise exceptions
    value = int(input("Enter a number: "))
    result = 10 / value
except ValueError:
    print("Please enter a valid number!")
except ZeroDivisionError:
    print("Cannot divide by zero!")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
else:
    print(f"Result: {result}")
finally:
    print("This always executes")
```

### Raising Exceptions:
```python
def validate_age(age):
    if age < 0:
        raise ValueError("Age cannot be negative!")
    return True
```

### Custom Exceptions:
```python
class MyCustomError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

try:
    raise MyCustomError("Something went wrong!")
except MyCustomError as e:
    print(f"Custom error: {e}")
```
            """,
            'post_type': 'code_example'
        },
        {
            'title': 'String Manipulation ',
            'caption': """
Python provides powerful string manipulation capabilities.

### Common String Methods:
```python
s = "  Hello, World!  "

# Case conversion
print(s.lower())       # '  hello, world!  '
print(s.upper())       # '  HELLO, WORLD!  '
print(s.title())       # '  Hello, World!  '

# Stripping whitespace
print(s.strip())       # 'Hello, World!'
print(s.lstrip())      # 'Hello, World!  '
print(s.rstrip())      # '  Hello, World!'

# Splitting and joining
words = "Python is awesome".split()  # ['Python', 'is', 'awesome']
print("-".join(words))              # 'Python-is-awesome'

# String formatting
name = "Alice"
age = 30
print(f"{name} is {age} years old")  # f-strings (Python 3.6+)
print("{} is {} years old".format(name, age))  # .format()

# String checks
print("hello".isalpha())    # True
print("123".isdigit())      # True
print(" ".isspace())        # True
```

### String Slicing:
```python
text = "Hello, Python!"
print(text[0])       # 'H'
print(text[7:13])    # 'Python'
print(text[::2])     # 'Hlo yhn'
print(text[::-1])    # '!nohtyP ,olleH'
```
            """,
            'post_type': 'code_example'
        },
        {
            'title': 'Sorting Algorithms ',
            'caption': """
## 1. Bubble Sort
- Simple but inefficient
- Time: O(n²) average/worst, O(n) best (already sorted)
- Space: O(1)

## 2. Selection Sort
- Finds minimum element, swaps with first position
- Time: O(n²) all cases
- Space: O(1)

## 3. Insertion Sort
- Builds final sorted array one item at a time
- Time: O(n²) average/worst, O(n) best
- Space: O(1)

## 4. Merge Sort
- Divide and conquer algorithm
- Time: O(n log n) all cases
- Space: O(n)

## 5. Quick Sort
- Divide and conquer with pivot element
- Time: O(n log n) average, O(n²) worst case
- Space: O(log n)

### Example (Quick Sort in Python):
```python
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
```
            """,
            'post_type': 'educational'
        },
        {
            'title': 'Big O Notation',
            'caption': """
Big O notation describes the performance of an algorithm in terms of how its runtime or space requirements grow as the input size grows.

### Common Time Complexities:
1. **O(1) - Constant Time**
   - Example: Accessing an array element by index

2. **O(log n) - Logarithmic Time**
   - Example: Binary search

3. **O(n) - Linear Time**
   - Example: Finding an element in an unsorted array

4. **O(n log n) - Linearithmic Time**
   - Example: Most efficient sorting algorithms (Merge Sort, Quick Sort)

5. **O(n²) - Quadratic Time**
   - Example: Bubble Sort, Selection Sort, Insertion Sort

6. **O(2^n) - Exponential Time**
   - Example: Recursive Fibonacci without memoization

### Space Complexity:
- Similar to time complexity but measures memory usage
- Example: O(n) space means memory usage grows linearly with input size

### Best, Average, Worst Case:
- **Best Case**: Minimum time/space required (best scenario)
- **Average Case**: Expected time/space for random input
- **Worst Case**: Maximum time/space required (worst scenario)

### Example Comparison:
```
Input Size (n) | O(1) | O(log n) | O(n) | O(n log n) | O(n²)
------------------------------------------------------------
10            |   1  |    1     |  10  |    10      | 100
100           |   1  |    2     | 100  |    200     | 10,000
1000          |   1  |    3     | 1000 |    3,000   | 1,000,000
```
            """,
            'post_type': 'educational'
        }
    ]
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create posts table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT NOT NULL,
        caption TEXT NOT NULL,
        post_type TEXT NOT NULL DEFAULT 'text',
        up INTEGER NOT NULL DEFAULT 0,
        down INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    # Add some upvotes and downvotes to make it look natural
    import random
    from datetime import datetime, timedelta
    
    for post in posts:
        # Set random creation date within the last 30 days
        days_ago = random.randint(0, 30)
        created_at = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Random upvotes (0-50) and downvotes (0-10)
        up = random.randint(0, 50)
        down = random.randint(0, 10)
        
        cursor.execute('''
        INSERT INTO posts (user_id, title, caption, post_type, up, down, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (admin_id, post['title'], post['caption'], post['post_type'], up, down, created_at))
    
    conn.commit()
    conn.close()
    print(f"Created {len(posts)} educational posts")

if __name__ == "__main__":
    # Initialize database if it doesn't exist
    from app import init_db
    init_db()
    
    # Create admin user and get their ID
    admin_id = create_admin_user()
    
    # Create educational posts
    create_posts(admin_id)
    
    print("Database seeding completed successfully!")
