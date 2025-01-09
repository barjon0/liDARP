from typing import Tuple

from utils.network.Line import Line


class Bus:
    def __init__(self, bus_id: int, capacity: int, line: Line, depot: Tuple[int]):
        self.id = bus_id
        self.capacity = capacity
        self.line = line
        self.depot = depot
