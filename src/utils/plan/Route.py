from typing import List


from utils.network.Bus import Bus
from utils.plan.RouteStop import RouteStop


class Route:
    def __init__(self, bus: Bus, stops: List[RouteStop]):
        self.bus = bus
        self.stops = stops
