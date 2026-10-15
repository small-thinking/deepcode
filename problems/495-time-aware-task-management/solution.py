import json


class SimpleTaskManager:
    def __init__(self):
        self.tasks = {}
        self.users = {}
        self.assignments = []

    def add_task(self, t, name, priority):
        number = len(self.tasks) + 1
        task_id = f"task_id_{number}"
        self.tasks[task_id] = {"name": name, "priority": priority, "number": number}
        return task_id

    def update_task(self, t, task_id, name, priority):
        if task_id not in self.tasks:
            return False
        self.tasks[task_id].update(name=name, priority=priority)
        return True

    def get_task(self, t, task_id):
        task = self.tasks.get(task_id)
        if task is None:
            return None
        return json.dumps({"name": task["name"], "priority": task["priority"]}, separators=(",", ":"))

    def _ordered_task_ids(self):
        return sorted(self.tasks, key=lambda task_id: (
            -self.tasks[task_id]["priority"], self.tasks[task_id]["number"]))

    def search_tasks(self, t, filter, max_results):
        if max_results <= 0:
            return []
        return [task_id for task_id in self._ordered_task_ids()
                if filter in self.tasks[task_id]["name"]][:max_results]

    def list_tasks_sorted(self, t, limit):
        return self._ordered_task_ids()[:max(limit, 0)]

    def add_user(self, t, user, quota):
        if user in self.users:
            return False
        self.users[user] = quota
        return True

    def _active(self, assignment, t):
        return not assignment["completed"] and assignment["start"] <= t < assignment["finish"]

    def assign_task(self, t, task_id, user, finish_time):
        if task_id not in self.tasks or user not in self.users:
            return False
        active_count = sum(self._active(a, t) for a in self.assignments if a["user"] == user)
        if active_count >= self.users[user]:
            return False
        self.assignments.append({"task_id": task_id, "user": user, "start": t,
                                 "finish": finish_time, "completed": False})
        return True

    def get_user_tasks(self, t, user):
        if user not in self.users:
            return []
        matches = [a for a in self.assignments if a["user"] == user and self._active(a, t)]
        matches.sort(key=lambda a: (a["finish"], a["start"]))
        return [a["task_id"] for a in matches]

    def complete_task(self, t, task_id, user):
        for assignment in self.assignments:
            if (assignment["task_id"] == task_id and assignment["user"] == user
                    and self._active(assignment, t)):
                assignment["completed"] = True
                return True
        return False

    def get_overdue_assignments(self, t, user):
        if user not in self.users:
            return []
        matches = [a for a in self.assignments
                   if a["user"] == user and not a["completed"] and a["finish"] <= t]
        matches.sort(key=lambda a: (a["finish"], a["start"]))
        return [a["task_id"] for a in matches]
