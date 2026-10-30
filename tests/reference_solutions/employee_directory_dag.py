class Node:
    def __init__(self, name, parents=None):
        self.name = name
        self.parents = list(parents) if parents is not None else []


def closest_common_groups(employees):
    def ancestors(employee):
        seen = set()
        stack = list(employee.parents)
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            stack.extend(node.parents)
        return seen

    common = ancestors(employees[0])
    for employee in employees[1:]:
        common.intersection_update(ancestors(employee))

    # Common ancestors are upward-closed, so a direct common child suffices
    # to disqualify a group even when the DAG has shortcut edges.
    non_lowest = {parent for group in common for parent in group.parents}
    return common - non_lowest
