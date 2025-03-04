from typing import List

from utils.helper.Timer import TimeImpl
from utils.network.Stop import Stop


class Line:
    def __init__(self, line_id: int, stops: List[Stop], depot: Stop, capacity: int, start_time: TimeImpl, end_time: TimeImpl):
        self.id = line_id
        self.stops = stops
        self.depot = depot
        self.capacity = capacity    # all buses on a line have the same capacity
        self.start_time = start_time
        self.end_time = end_time
