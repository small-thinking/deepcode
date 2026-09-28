def solution(orders, products, categories):
    product_category = {row['product_id']: row['category_id'] for row in products}
    category_name = {row['category_id']: row['category_name'] for row in categories}
    totals = {}

    for order in orders:
        category_id = product_category.get(order['product_id'])
        if category_id not in category_name:
            continue
        name = category_name[category_id]
        sales, count, completed = totals.get(name, (0, 0, 0))
        totals[name] = (
            sales + order['quantity'] * order['unit_price'],
            count + 1,
            completed + (order['status'] == 'completed'),
        )

    return [
        {'category_name': name, 'total_sales': sales,
         'average_sales_per_order': sales / count,
         'completion_rate': completed / count}
        for name, (sales, count, completed) in sorted(totals.items())
    ]
