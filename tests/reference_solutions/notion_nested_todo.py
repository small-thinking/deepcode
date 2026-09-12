class NestedTodoList:
    def __init__(self):
        self.items = {}
        self.roots = []

    def add(self, item_id, text, parent_id=None):
        if item_id in self.items:
            raise ValueError('duplicate item ID')
        if parent_id is not None and parent_id not in self.items:
            raise ValueError('unknown parent')
        self.items[item_id] = {'text': text, 'done': False, 'children': []}
        siblings = self.roots if parent_id is None else self.items[parent_id]['children']
        siblings.append(item_id)

    def set_done(self, item_id, done):
        if item_id not in self.items:
            raise ValueError('unknown item')
        self.items[item_id]['done'] = done

    def list_items(self):
        result = []
        stack = [(item_id, 0) for item_id in reversed(self.roots)]
        while stack:
            item_id, depth = stack.pop()
            item = self.items[item_id]
            result.append((item_id, item['text'], item['done'], depth))
            stack.extend((child_id, depth + 1) for child_id in reversed(item['children']))
        return result
