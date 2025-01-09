from utils.demand.AbstractRequest import AbstractRequest
from utils.network.Stop import Stop


class SplitRequest(AbstractRequest):
    def __init__(self, parent_id: int, variation_id: int, pick_up_location: Stop, drop_off_location: Stop):
        self.variation_id = variation_id
        super().__init__(parent_id, pick_up_location, drop_off_location)
