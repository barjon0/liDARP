from typing import Tuple


class Stop:
    def __init__(self, stop_id: int, coordinates: Tuple[int, int]):
        self.id = stop_id
        self.coordinates = coordinates

    def __repr__(self):
        return f"Stop(id: {self.id}, coordinateX: {self.coordinates[0]}, coordinateY: {self.coordinates[1]})"