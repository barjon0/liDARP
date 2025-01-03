from utils.network.Stop import Stop


class AbstractRequest:
    def __init__(self, request_id: int, pick_up_location: Stop, drop_off_location: Stop):
        self.id = request_id
        self.pick_up_location = pick_up_location
        self.drop_off_location = drop_off_location
        self.act_start_time = None
        self.act_end_time = None
