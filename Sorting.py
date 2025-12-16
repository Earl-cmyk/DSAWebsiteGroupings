import random

ARRAY_SIZE = 20
MIN_VALUE = 5
MAX_VALUE = 95


def random_array():
    return [random.randint(MIN_VALUE, MAX_VALUE) for _ in range(ARRAY_SIZE)]


# BUBBLE SORT
def bubble_step(state):
    a = state["arr"]
    i, j = state["i"], state["j"]

    if state["done"]:
        return state, [], True

    if j < len(a) - i - 1:
        if a[j] > a[j + 1]:
            a[j], a[j + 1] = a[j + 1], a[j]
        state["j"] += 1
        highlight = [j, j + 1]
    else:
        state["j"] = 0
        state["i"] += 1
        highlight = []

    if state["i"] >= len(a) - 1:
        state["done"] = True

    return state, highlight, state["done"]


# MERGE SORT (steps)
def merge_sort_steps(arr):
    steps = []

    def merge_sort(a, l, r):
        if l >= r:
            return
        m = (l + r) // 2
        merge_sort(a, l, m)
        merge_sort(a, m + 1, r)
        merge(a, l, m, r)

    def merge(a, l, m, r):
        left = a[l:m+1]
        right = a[m+1:r+1]

        i = j = 0
        k = l

        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                a[k] = left[i]
                i += 1
            else:
                a[k] = right[j]
                j += 1
            steps.append((a.copy(), [k]))
            k += 1

        while i < len(left):
            a[k] = left[i]
            steps.append((a.copy(), [k]))
            i += 1
            k += 1

        while j < len(right):
            a[k] = right[j]
            steps.append((a.copy(), [k]))
            j += 1
            k += 1

    arr = arr.copy()
    merge_sort(arr, 0, len(arr) - 1)
    return steps


# QUICK SORT (steps)
def quick_sort_steps(arr):
    steps = []

    def quicksort(a, low, high):
        if low < high:
            p = partition(a, low, high)
            quicksort(a, low, p - 1)
            quicksort(a, p + 1, high)

    def partition(a, low, high):
        pivot = a[high]
        i = low
        for j in range(low, high):
            if a[j] <= pivot:
                a[i], a[j] = a[j], a[i]
                steps.append((a.copy(), [i, j]))
                i += 1
        a[i], a[high] = a[high], a[i]
        steps.append((a.copy(), [i, high]))
        return i

    arr = arr.copy()
    quicksort(arr, 0, len(arr) - 1)
    return steps


def insertion_sort_steps(arr):
    steps = []
    a = arr.copy()

    for i in range(1, len(a)):
        key = a[i]
        j = i - 1

        while j >= 0 and a[j] > key:
            a[j + 1] = a[j]
            steps.append((a.copy(), [j, j + 1]))
            j -= 1

        a[j + 1] = key
        steps.append((a.copy(), [j + 1]))

    return steps


# SELECTION SORT (steps)
def selection_sort_steps(arr):
    steps = []
    a = arr.copy()
    n = len(a)

    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if a[j] < a[min_idx]:
                min_idx = j

        if min_idx != i:
            a[i], a[min_idx] = a[min_idx], a[i]
            steps.append((a.copy(), [i, min_idx]))

    return steps
