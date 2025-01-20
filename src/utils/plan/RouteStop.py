from datetime import time
from typing import Set

from utils.demand.Request import Request
from utils.network.Bus import Bus
from utils.network.Stop import Stop


class RouteStop:
    def __init__(self, stop: Stop, arriv_time: time, depart_time: time, pick_up: Set[Request], drop_off: Set[Request], bus: Bus):
        self.stop = stop
        self.arriv_time = arriv_time
        self.depart_time = depart_time
        self.pick_up = pick_up
        self.drop_off = drop_off
        self.bus = bus
