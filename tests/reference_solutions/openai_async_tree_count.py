class AsyncTreeCounter:
    def __init__(self, node_id, child_ids, send_async_message):
        self.node_id = node_id
        self.child_ids = list(child_ids)
        self.send_async_message = send_async_message
        self.state = {}

    def receive_message(self, from_node_id, message):
        request_id = message["request_id"]
        if message["type"] == "count_request":
            pending = set(self.child_ids)
            self.state[request_id] = {
                "parent_id": from_node_id,
                "pending_children": pending,
                "count": 1,
            }
            if not pending:
                self._reply(request_id)
                return
            for child_id in self.child_ids:
                self.send_async_message(
                    child_id,
                    {"type": "count_request", "request_id": request_id},
                )
            return

        if message["type"] != "count_reply":
            raise ValueError("unknown message type")
        current = self.state[request_id]
        if from_node_id not in current["pending_children"]:
            return
        current["pending_children"].remove(from_node_id)
        current["count"] += message["count"]
        if not current["pending_children"]:
            self._reply(request_id)

    def _reply(self, request_id):
        current = self.state.pop(request_id)
        self.send_async_message(
            current["parent_id"],
            {
                "type": "count_reply",
                "request_id": request_id,
                "count": current["count"],
            },
        )
