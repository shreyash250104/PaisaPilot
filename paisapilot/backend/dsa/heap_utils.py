import heapq

def top_n(items, n, key):
    """Largest n items using a min-heap of size n: O(M log N)."""
    heap = []
    for i, item in enumerate(items):
        entry = (key(item), i, item)      # i breaks ties
        if len(heap) < n:
            heapq.heappush(heap, entry)
        elif entry[0] > heap[0][0]:
            heapq.heapreplace(heap, entry)
    return [e[2] for e in sorted(heap, reverse=True)]