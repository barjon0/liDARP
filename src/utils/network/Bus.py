from typing import Tuple

from utils.network.Line import Line
from utils.network.Stop import Stop


class Bus:
    def __init__(self, bus_id: int, line: Line):
        self.id = bus_id
        self.line = line

    def __str__(self):
        return str(self.id)
