from typing import Set

import Global
from utils.demand.Request import Request
from utils.helper import Helper
from utils.helper.Timer import TimeImpl
from utils.network.Bus import Bus
from utils.network.Stop import Stop


class RouteStop:
    def __init__(self, stop: Stop, arriv_time: TimeImpl, depart_time: TimeImpl, bus: Bus):
        self.stop = stop
        self.arriv_time = arriv_time
        self.depart_time = depart_time
        self.pick_up = set()
        self.drop_off = set()
        self.bus = bus

    def to_output(self):
        return [self.stop.id, str(self.arriv_time), str(self.depart_time), str(self.pick_up), str(self.drop_off)]

    def __repr__(self):
        return f"RouteStop(Bus: {self.bus.id}, Location: {self.stop.id}, PickUp: {self.pick_up}, DropOff: {self.drop_off})"
