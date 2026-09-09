def completion_rate(orders, city, order_type):
    total = completed = 0
    for row in orders:
        if row['city'] == city and row['order_type'] == order_type:
            total += 1
            completed += row['status'] == 'completed'
    return completed / total if total else 0.0
