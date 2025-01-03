from typing import List
import Stop


class Line:
    def __int__(self, line_id: int, stops: List[Stop]):
        self.id = line_id
        self.stops = stops
