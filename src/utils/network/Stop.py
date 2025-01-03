from typing import Tuple


class Stop:
    def __int__(self, stop_id: int, coordinates: Tuple[int]):
        self.id = stop_id
        self.coordinates = coordinates
