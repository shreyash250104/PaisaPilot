import heapq

def simplify(net):
    """net: {user_id: paid - owed}. Returns [(from_user, to_user, amount)]."""
    creditors = [(-amt, u) for u, amt in net.items() if amt > 0]
    debtors = [(amt, u) for u, amt in net.items() if amt < 0]
    heapq.heapify(creditors)      # largest credit first
    heapq.heapify(debtors)        # largest debt first (most negative)
    payments = []
    while creditors and debtors:
        c_neg, c = heapq.heappop(creditors)
        d_neg, d = heapq.heappop(debtors)
        credit, debt = -c_neg, -d_neg
        pay = min(credit, debt)
        payments.append((d, c, pay))
        if credit > pay:
            heapq.heappush(creditors, (-(credit - pay), c))
        if debt > pay:
            heapq.heappush(debtors, (-(debt - pay), d))
    return payments