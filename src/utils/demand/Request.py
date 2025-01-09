from datetime import time
from typing import List, Dict

from utils.demand.AbstractRequest import AbstractRequest
from utils.demand.SplitRequest import SplitRequest
from utils.network.Stop import Stop


class Request(AbstractRequest):

    def __init__(self, request_id: int, pick_up_location: Stop, drop_off_location: Stop, earl_start_time: time, latest_arr_time: time, register_time: time):
        self.earl_start_time = earl_start_time
        self.latest_arr_time = latest_arr_time
        self.register_time = register_time
        self.split_requests: Dict[int, List[SplitRequest]] = {}
        super().__init__(request_id, pick_up_location, drop_off_location)

    def split_request(self):
        pass
