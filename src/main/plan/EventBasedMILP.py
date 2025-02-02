from datetime import time
from typing import List, Set, Dict, Tuple

from main.plan.Planner import Planner
from utils.demand.Request import Request

from utils.demand.SplitRequest import SplitRequest
from utils.helper.EventGraph import EventGraph
from utils.helper.LineGraph import LineGraph
from utils.network.Bus import Bus
from utils.network.Line import Line
from utils.network.Stop import Stop


def check_dir(split_req: SplitRequest):
    line: Line = split_req.line
    start_idx = line.stops.index(split_req.pick_up_location)
    end_idx = line.stops.index(split_req.drop_off_location)
    if start_idx < end_idx:
        return 0
    else:
        return 1


def check_on_route(split: SplitRequest, search_loc: Stop):
    line: Line = split.line

    idx_start = line.stops.index(split.pick_up_location)
    idx_end = line.stops.index(split.drop_off_location)
    idx_search = line.stops.index(search_loc)

    if idx_start < idx_end:
        if idx_start <= idx_search <= idx_end:
            return True
    elif idx_start >= idx_search >= idx_end:
        return True

    return False


def iterate_sweep_line(queue: dict, event_points: list, input_points):
    status_set: Set[SplitRequest] = set()
    output_dict: Dict[SplitRequest, Tuple[Set[SplitRequest], Set[SplitRequest]]] = {x: (set(), set()) for x in
                                                                                    input_points}

    for stop in event_points:
        for req_ins in queue[stop][0]:
            for other in status_set | queue[stop][0]:
                if other.id != req_ins.id:
                    output_dict[req_ins][0].add(other)

        status_set |= queue[stop][0]

        for req_del in queue[stop][1]:
            for other in status_set:
                if other.id is not req_del.id:
                    output_dict[req_del][1].add(other)

        status_set -= queue[stop][1]

    return output_dict


def sweep_line_local(splits_in_dir: Set[SplitRequest], line: Line, direction: int):
    # extract event points(make queue with insert and delete objects) -> go trough queue -> update status_dict -> build output from keys
    queue: Dict[Stop, Tuple[Set[SplitRequest], Set[SplitRequest]]] = {x: (set(), set()) for x in line.stops}

    for split_req in splits_in_dir:
        queue[split_req.pick_up_location][0].add(split_req)
        queue[split_req.drop_off_location][1].add(split_req)

    event_points: List[Stop] = line.stops.copy()
    if direction == 1:
        event_points.reverse()

    return iterate_sweep_line(queue, event_points, splits_in_dir)


def sweep_line_time(splits_in_dir: Set[SplitRequest]):
    queue: Dict[time, Tuple[Set[SplitRequest], Set[SplitRequest]]] = \
        {x.earl_start_time: (set(), set()) for x in splits_in_dir}
    queue |= {x.latest_arr_time: (set(), set()) for x in splits_in_dir}

    for split_req in splits_in_dir:
        queue[split_req.earl_start_time][0].add(split_req)
        queue[split_req.latest_arr_time][1].add(split_req)

    event_points = sorted(queue.keys())
    return iterate_sweep_line(queue, event_points, splits_in_dir)


class EventBasedMILP(Planner):
    def __init__(self, bus_list: List[Bus], network_graph: LineGraph):
        super().__init__(bus_list, network_graph)
        self.event_graph: EventGraph

    def walk_route(self, req: Request, bus_user_dict: Dict[Bus, Set[Request]], next_bus_locations: Dict[Bus, Stop]):
        # find current position -> walk among selected route to position -> return all future splits
        bus: Bus = next(k for k, v in bus_user_dict if req in v)

        curr_location: Stop = next_bus_locations[bus]

        result = {}
        found: bool = False
        for split in req.split_requests[req.route_int]:
            if not found:
                if split.line == bus.line:
                    split.in_action = True
                    if check_on_route(split, curr_location):
                        found = True
                        result += split
                else:
                    split.in_action = True
            else:
                result += split

        return result

    # for dynamic implementation:
    # find all active Requests(splitRequests) -> curr_waiting + new + passengers    and all poss. splitRequests
    def make_plan(self, new_requests: Set[Request], next_bus_locations: Dict[Bus, Stop],
                  bus_user_dict: Dict[Bus, Set[Request]], wait_user_locations: Dict[Request, Stop],
                  bus_delay: Dict[Bus, float]):
        all_active_requests: Set[Request] = set()
        all_active_requests |= new_requests | wait_user_locations.keys()

        all_follow_splits: Set[SplitRequest] = set()
        for req in all_active_requests:
            for opt in req.split_requests.keys():
                all_follow_splits |= set(req.split_requests[opt])

        curr_passengers: Set[Request] = set().union(*bus_user_dict.values())
        all_active_requests |= curr_passengers

        for req in curr_passengers:
            all_follow_splits |= self.walk_route(req, bus_user_dict, next_bus_locations)

        # build candidate sets for lines and directions
        line_dir_dict: Dict[Line, Tuple[Set[SplitRequest]]] = {x: [set(), set()] for x in self.network_graph.all_lines}
        for split_req in all_follow_splits:
            direction = check_dir(split_req)
            line_dir_dict[split_req.line][direction].add(split_req)

        for line in line_dir_dict.keys():
            for direction in range(2):
                # direction 0 is normal, 1 is reverse
                # local_cand_map generate pick_up candidates and drop off candidates
                local_cand_dict: Dict[SplitRequest, Tuple[Set[SplitRequest], Set[SplitRequest]]] = \
                    sweep_line_local(line_dir_dict[line][direction], line, direction)

                time_cand_dict: Dict[SplitRequest, Tuple[Set[SplitRequest], Set[SplitRequest]]] = sweep_line_time(
                    line_dir_dict[line][direction])

                agg_cand_dict: Dict[SplitRequest, Tuple[Set[SplitRequest], Set[SplitRequest]]] = {}
                for split_req in local_cand_dict.keys():
                    agg_cand_dict[split_req] = (local_cand_dict[split_req][0] & time_cand_dict[split_req][0],
                                                local_cand_dict[split_req][1] & time_cand_dict[split_req][1])

                print("soo??")
                # make permutations (check if some split_requests already started)
        # build event graph (might already exist)

        # add edges to event graph
        # build lin. model
        # solve model
        # convert to route solution
        pass
