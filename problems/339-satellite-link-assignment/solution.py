from math import cos, radians, sqrt


_COS_45 = cos(radians(45))
_COS_10 = cos(radians(10))


def _subtract(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _visible(user, satellite):
    direction = _subtract(satellite, user)
    return _dot(user, direction) >= _COS_45 * sqrt(_dot(user, user) * _dot(direction, direction))


def _conflicts(first_beam, second_beam):
    return _dot(first_beam, second_beam) > _COS_10 * sqrt(
        _dot(first_beam, first_beam) * _dot(second_beam, second_beam)
    )


def assign_links(users, satellites):
    """Greedily place constrained users, checking visibility, capacity, and frequencies.

    The checks guarantee feasibility; the greedy order does not guarantee maximum coverage.
    """
    choices = {
        user_id: [satellite_id for satellite_id, satellite in satellites.items()
                  if _visible(user, satellite)]
        for user_id, user in users.items()
    }
    assignments = {}
    beams = {satellite_id: [] for satellite_id in satellites}
    for user_id in sorted(users, key=lambda uid: len(choices[uid])):
        user = users[user_id]
        for satellite_id in sorted(choices[user_id], key=lambda sid: len(beams[sid])):
            used = beams[satellite_id]
            if len(used) >= 32:
                continue
            beam = _subtract(user, satellites[satellite_id])
            frequency = next(
                (frequency for frequency in range(1, 5)
                 if all(old_frequency != frequency or not _conflicts(beam, old_beam)
                        for old_beam, old_frequency in used)),
                None,
            )
            if frequency is not None:
                assignments[user_id] = (satellite_id, frequency)
                used.append((beam, frequency))
                break
    return assignments
