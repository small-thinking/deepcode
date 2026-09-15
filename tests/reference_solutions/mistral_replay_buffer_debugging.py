import random


MAX_SAMPLE_COUNT = 2


class ReplayBuffer:
    def __init__(self, buffer_size):
        self.buffer = []
        self.buffer_size = buffer_size
        self.last_state = None

    def add(self, state, action, reward, next_state, done):
        experience = {
            "state": state,
            "action": action,
            "reward": reward,
            "next_state": next_state,
            "done": done,
            "sample_count": 0,
        }
        self.last_state = state
        if len(self.buffer) >= self.buffer_size:
            self.buffer[random.randrange(self.buffer_size)] = experience
        else:
            self.buffer.append(experience)

    def add_batch(self, states, actions, rewards, next_states, dones):
        for state, action, reward, next_state, done in zip(
            states, actions, rewards, next_states, dones
        ):
            self.add(state, action, reward, next_state, done)

    def sample(self):
        index = random.randrange(len(self.buffer))
        experience = self.buffer[index]
        result = tuple(
            experience[key]
            for key in ("state", "action", "reward", "next_state", "done")
        )
        experience["sample_count"] += 1
        if experience["sample_count"] >= MAX_SAMPLE_COUNT:
            self.buffer.pop(index)
        return result

    def get_last_state(self):
        return self.last_state
