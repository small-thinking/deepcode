import heapq


def solution(operations):
    players = {}
    leaderboard = []
    outputs = []

    def add_snapshot(player_id):
        player = players[player_id]
        heapq.heappush(leaderboard, (-player["score"], player_id, player["version"]))

    for operation in operations:
        kind = operation[0]
        if kind == "addPlayer":
            player_id = operation[1]
            if player_id not in players:
                players[player_id] = {"room": 0, "score": 0, "version": 0}
                add_snapshot(player_id)
        elif kind == "recordTask":
            player_id, room_id, points = operation[1:]
            player = players.get(player_id)
            if player is not None and player["room"] == room_id:
                player["score"] += points
                player["version"] += 1
                add_snapshot(player_id)
        elif kind == "moveToNextRoom":
            player = players.get(operation[1])
            if player is not None:
                player["room"] += 1
        elif kind == "getPlayerState":
            player = players.get(operation[1])
            outputs.append(None if player is None else {"room": player["room"], "score": player["score"]})
        elif kind == "topK":
            selected = []
            while leaderboard and len(selected) < operation[1]:
                score, player_id, version = heapq.heappop(leaderboard)
                if players[player_id]["version"] == version:
                    selected.append((score, player_id, version))
            outputs.append([player_id for _, player_id, _ in selected])
            for entry in selected:
                heapq.heappush(leaderboard, entry)
    return outputs
