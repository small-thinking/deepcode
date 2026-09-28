def match_stream(lines):
    queries = []
    output = []

    for line in lines:
        assert isinstance(line, str)
        if line.startswith('Q: '):
            text = line[3:]
            words = set(text.casefold().split())
            assert text and words
            query_id = len(queries) + 1
            queries.append((query_id, words))
            output.append(f'ACK: {text}; ID={query_id}')
        elif line.startswith('L: '):
            text = line[3:]
            log_words = set(text.casefold().split())
            matching_ids = [query_id for query_id, words in queries if words <= log_words]
            if matching_ids:
                ids = ','.join(str(query_id) for query_id in matching_ids)
                output.append(f'M: {text}; Q={ids}')
        else:
            raise AssertionError('line must start with Q: or L:')

    return output
