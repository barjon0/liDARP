import math
from dataclasses import dataclass

import Global


def convert_2_time(duration_min: float):
    hours: int = math.floor(duration_min / 60)

    minutes: int = math.floor(duration_min) % 60
    if round(duration_min) > math.floor(duration_min):
        if minutes == 59:
            minutes = 0
            hours += 1
        else:
            minutes += 1

    if hours > 23:
        ValueError("time overflow occured")

    return TimeImpl(hours, minutes)


def calc_time(distance: float) -> float:
    return (distance * 60) / Global.AVERAGE_KMH


def conv_time_to_dist(duration: float):
    return (duration * Global.AVERAGE_KMH) / 60


def conv_string_2_Time(time_string: str):
    attr = time_string.split(":")
    assert len(attr) == 3
    return TimeImpl(int(attr[0]), int(attr[1]), int(attr[2]))


@dataclass(frozen=True)
class TimeImpl:
    hour: int
    minute: int
    second: int = 0

    def __post_init__(self):
        if 0 <= self.hour <= 23:
            if 0 <= self.minute <= 59:
                if not (0 <= self.second <= 59):
                    ValueError(f"second not in range 0 to 60; was {self.second}")
            else:
                ValueError(f"minute not in range 0 to 60; was {self.minute}")
        else:
            ValueError(f"hour not in range 0 to 23; was {self.second}")

    def get_in_minutes(self):
        sum_min: float = 0

        sum_min += 60 * self.hour
        sum_min += self.minute
        sum_min += self.second / 60

        return sum_min

    def __add__(self, other):
        assert isinstance(other, TimeImpl)
        return convert_2_time(self.get_in_minutes() + other.get_in_minutes())

    def __sub__(self, other):
        assert isinstance(other, TimeImpl)
        return convert_2_time(self.get_in_minutes() - other.get_in_minutes())

    def __str__(self):
        return f"{self.hour}:{self.minute}:{self.second}"

    def __lt__(self, other):
        assert isinstance(other, TimeImpl)
        if self.get_in_minutes() < other.get_in_minutes():
            return True
        else:
            return False

    def __gt__(self, other):
        assert isinstance(other, TimeImpl)
        if self.get_in_minutes() > other.get_in_minutes():
            return True
        else:
            return False

    def __eq__(self, other):
        assert isinstance(other, TimeImpl)
        if self.get_in_minutes() == other.get_in_minutes():
            return True
        else:
            return False

    def __le__(self, other):
        assert isinstance(other, TimeImpl)
        if self.get_in_minutes() <= other.get_in_minutes():
            return True
        else:
            return False

    def __ge__(self, other):
        assert isinstance(other, TimeImpl)
        if self.get_in_minutes() >= other.get_in_minutes():
            return True
        else:
            return False

    def add_minutes(self, minutes: float):
        return convert_2_time(self.get_in_minutes() + minutes)

    def sub_minutes(self, minutes: float):
        return convert_2_time(self.get_in_minutes() - minutes)
