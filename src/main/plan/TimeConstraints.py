import Global
from utils.demand.AbstractRequest import SplitRequest


class AbstractConstraintMaker():
    def create_variables(self, split_req: SplitRequest):
        pass

    def get_big_m(self, prec_split: SplitRequest, prec_bool: bool, duration, suc_absolute: float):
        pass

    def add_value(self, split_req: SplitRequest, start_bool: bool):
        pass

    def add_value_line_start(self, line_start):
        pass



class AbsoluteValueConstraints(AbstractConstraintMaker):
    def create_variables(self, split_req: SplitRequest):
        return [{"names": [f"B_{split_req.split_id}+"], "lb": [split_req.earl_start_time.get_in_minutes()],
                 "ub": [split_req.latest_start_time.get_in_minutes()]},
                {"names": [f"B_{split_req.split_id}-"], "lb": [split_req.earl_arr_time.get_in_minutes()],
                 "ub": [split_req.latest_arr_time.get_in_minutes()]}]

    def get_big_m(self, prec_split: SplitRequest, prec_bool: bool, duration, suc_absolute: float):
        return int(prec_split.line.end_time.get_in_minutes())

    def add_value(self, split_req: SplitRequest, start_bool: bool):
        return 0

class RelativeConstraints(AbstractConstraintMaker):
    def create_variables(self, split_req: SplitRequest):
        return [{"names": [f"B_{split_req.split_id}+"], "lb": [0],
                 "ub": [split_req.latest_start_time.get_in_minutes() - split_req.earl_start_time.get_in_minutes()]},
                {"names": [f"B_{split_req.split_id}-"], "lb": [0],
                 "ub": [split_req.latest_arr_time.get_in_minutes() - split_req.earl_arr_time.get_in_minutes()]}]

    def add_value(self, split_req: SplitRequest, start_bool: bool):
        if start_bool:
            return split_req.earl_start_time.get_in_minutes()
        else:
            return split_req.earl_arr_time.get_in_minutes()

    def get_big_m(self, prec_split: SplitRequest, prec_bool: bool, duration, suc_absolute: float):

        max_rel: float
        if prec_bool:
            max_rel = prec_split.latest_start_time.get_in_minutes() - prec_split.earl_start_time.get_in_minutes()
        else:
            max_rel = prec_split.latest_arr_time.get_in_minutes() - prec_split.earl_arr_time.get_in_minutes()

        return max_rel + duration + Global.TRANSFER_MINUTES + max(0, self.add_value(prec_split, prec_bool) - suc_absolute)

