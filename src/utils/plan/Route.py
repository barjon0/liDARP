from typing import List

import RouteStop
from utils.network.Bus import Bus


class Route:
    def __init__(self, bus: Bus, stops: List[RouteStop]):
        self.bus = bus
        self.stops = stops
