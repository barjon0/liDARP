from datetime import time
from typing import Set

from utils.demand.Request import Request
from utils.helper import Helper
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

    def to_output(self):
        return [self.stop.id, Helper.time_to_string(self.arriv_time), Helper.time_to_string(self.depart_time), str({self.pick_up}), str(self.drop_off)]
