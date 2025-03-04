from typing import List, Dict

import Global
from utils.demand.AbstractRequest import AbstractRequest
from utils.demand.SplitRequest import SplitRequest
from utils.helper import Timer
from utils.helper.Timer import TimeImpl
from utils.network.Stop import Stop


class Request(AbstractRequest):

    def __init__(self, request_id: int, number_of_passengers: int, pick_up_location: Stop, drop_off_location: Stop, earl_start_time: TimeImpl,
                 latest_arr_time: TimeImpl, register_time: TimeImpl, numb_transfer: int, km_planned: float):
        self.register_time = register_time
        self.split_requests: Dict[int, List[SplitRequest]] = {}
        self.numb_transfer = numb_transfer      # number of transfers in shortest route
        self.km_planned = km_planned            # km needed for shortest route

        self.route_int: int = None    # none at first, when solution selected(idx of split_request_dict) -> fill with number, as soon as picked_up -> final
        super().__init__(request_id, number_of_passengers, pick_up_location, drop_off_location, earl_start_time, latest_arr_time)
        self.latest_start_time = self.earl_start_time.add_minutes(Global.TIME_WINDOW)
        self.earl_arr_time = self.earl_start_time.add_minutes(Timer.calc_time(self.km_planned) + (self.numb_transfer * Global.TRANSFER_MINUTES))

    def __str__(self):
        return f"{self.id}"

    def __repr__(self):
        return f"Request(id:{self.id}, start:{self.pick_up_location.id}, end:{self.drop_off_location.id})"
