from typing import List

from utils.network.Stop import Stop


class Line:
    def __init__(self, line_id: int, stops: List[Stop]):
        self.id = line_id
        self.stops = stops
