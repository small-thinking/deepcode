def get_comments_to_exclude(comments, mode):
    children = {comment_id: [] for comment_id in comments}
    roots = []
    for comment_id, comment in comments.items():
        parent = comment['parent_comment']
        if parent is None:
            roots.append(comment_id)
        else:
            children[parent].append(comment_id)

    excluded = set()
    stack = [(root, False) for root in roots]
    unwanted = 'dog' if mode == 'CAT_PERSON' else 'cat'
    while stack:
        comment_id, ancestor_hidden = stack.pop()
        hidden = ancestor_hidden or comments[comment_id][unwanted]
        if hidden:
            excluded.add(comment_id)
        stack.extend((child, hidden) for child in children[comment_id])
    return excluded
