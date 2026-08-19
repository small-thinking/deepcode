from collections import defaultdict


def capacity_utilization_report(rows, region=None, minimum_utilization=0.0):
    totals = defaultdict(lambda: [0, 0])

    for row in rows:
        if row["status"] != "active":
            continue
        if region is not None and row["region"] != region:
            continue
        total = totals[row["service"]]
        total[0] += row["capacity_units"]
        total[1] += row["reserved_units"]

    report = []
    for service, (total_capacity, total_reserved) in totals.items():
        if total_capacity == 0:
            continue
        utilization = total_reserved / total_capacity
        if utilization < minimum_utilization:
            continue
        report.append((service, total_capacity, total_reserved, utilization))

    report.sort(key=lambda item: (-item[3], -item[2], item[0]))
    return [
        (service, total_capacity, total_reserved, round(utilization, 4))
        for service, total_capacity, total_reserved, utilization in report
    ]
