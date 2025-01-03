import Line


class Bus:
    def __int__(self, bus_id: int, capacity: int, line: Line):
        self.id = bus_id
        self.capacity = capacity
        self.line = line
