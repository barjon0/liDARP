from datetime import time

from utils.network.Stop import Stop


class AbstractRequest:
    def __init__(self, request_id: int, pick_up_location: Stop, drop_off_location: Stop, earl_start_time: time = None,
                 latest_arr_time: time = None):
        self.id = request_id
        self.pick_up_location = pick_up_location
        self.drop_off_location = drop_off_location
        self.earl_start_time = earl_start_time
        self.latest_arr_time = latest_arr_time
        self.act_start_time = None
        self.act_end_time = None
