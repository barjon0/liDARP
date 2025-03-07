from typing import Dict, List

import Global
from utils.helper import Timer
from utils.helper.Timer import TimeImpl
from utils.network.Line import Line
from utils.network.Stop import Stop


class AbstractRequest:
    def __init__(self, request_id: int, number_of_passengers: int, pick_up_location: Stop, drop_off_location: Stop, earl_start_time: TimeImpl = None,
                 latest_arr_time: TimeImpl = None):
        self.id = request_id
        self.pick_up_location = pick_up_location
        self.drop_off_location = drop_off_location
        self.earl_start_time = earl_start_time
        self.latest_arr_time = latest_arr_time
        self.number_of_passengers = number_of_passengers
        self.latest_start_time = None
        self.earl_arr_time = None
        self.act_start_time = None
        self.act_end_time = None


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
        return str(self.id)

    def __repr__(self):
        return f"Request(id:{self.id}, start:{self.pick_up_location.id}, end:{self.drop_off_location.id})"


class SplitRequest(AbstractRequest):
    id_counter = 0

    def __init__(self, parent_req: Request, pick_up_location: Stop, drop_off_location: Stop, used_line: Line,
                 number_of_passengers: int):
        self.line = used_line
        self.parent = parent_req
        self.in_action: bool = False  # declare if split_request already started or finished(maybe add start and end times?)
        self.split_id = SplitRequest.id_counter
        SplitRequest.id_counter += 1
        super().__init__(parent_req.id, number_of_passengers, pick_up_location, drop_off_location)

    def __repr__(self):
        return f"SplitRequest(id:{self.id}; line:{self.line.id}; pick-up:{self.pick_up_location.id}; drop-off:{self.drop_off_location.id})"

