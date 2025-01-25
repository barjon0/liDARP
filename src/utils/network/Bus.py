from typing import Tuple

from utils.network.Line import Line
from utils.network.Stop import Stop


class Bus:
    def __init__(self, bus_id: int, capacity: int, line: Line, depot: Stop):
        self.id = bus_id
        self.capacity = capacity
        self.line = line
        self.depot = depot

    def __str__(self):
        return str(self.id)
