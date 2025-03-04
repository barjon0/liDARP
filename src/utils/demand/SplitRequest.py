from utils.demand.AbstractRequest import AbstractRequest
from utils.network.Line import Line
from utils.network.Stop import Stop


class SplitRequest(AbstractRequest):
    id_counter = 0

    def __init__(self, parent_req: AbstractRequest, pick_up_location: Stop, drop_off_location: Stop, used_line: Line,
                 number_of_passengers: int):
        self.line = used_line
        self.parent = parent_req
        self.in_action: bool = False  # declare if split_request already started or finished(maybe add start and end times?)
        self.split_id = SplitRequest.id_counter
        SplitRequest.id_counter += 1
        super().__init__(parent_req.id, number_of_passengers, pick_up_location, drop_off_location)

    def __repr__(self):
        return f"SplitRequest(id:{self.id}; line:{self.line.id}; pick-up:{self.pick_up_location.id}; drop-off:{self.drop_off_location.id})"
