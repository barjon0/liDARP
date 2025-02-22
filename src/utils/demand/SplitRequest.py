from utils.demand.AbstractRequest import AbstractRequest
from utils.network.Line import Line
from utils.network.Stop import Stop


class SplitRequest(AbstractRequest):
    def __init__(self, parent_id: int, pick_up_location: Stop, drop_off_location: Stop, used_line: Line):
        self.line = used_line
        self.in_action: bool = False        # declare if split_request already started or finished(maybe add start and end times?)
        super().__init__(parent_id, pick_up_location, drop_off_location)

    def __repr__(self):
        return f"SplitRequest(id:{self.id}; line:{self.line.id}; pick-up:{self.pick_up_location.id}; drop-off:{self.drop_off_location.id})"
