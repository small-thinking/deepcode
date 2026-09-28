def total_size(tree, path='/'):
    def validate(directory):
        assert isinstance(directory, dict)
        for name, child in directory.items():
            assert isinstance(name, str) and name not in ('', '.', '..') and '/' not in name
            if isinstance(child, dict):
                validate(child)
            else:
                assert type(child) is int and child >= 0

    assert isinstance(tree, dict)
    assert isinstance(path, str)
    validate(tree)

    stripped = path.strip('/')
    parts = [] if stripped == '' else stripped.split('/')
    assert all(part not in ('', '.', '..') for part in parts)

    node = tree
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]

    def sum_directory(directory):
        total = 0
        for child in directory.values():
            total += sum_directory(child) if isinstance(child, dict) else child
        return total

    return sum_directory(node) if isinstance(node, dict) else node
