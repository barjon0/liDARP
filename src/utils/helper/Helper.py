import math
from datetime import time
from typing import Dict, Set, List

from utils.demand.Request import Request
from utils.demand.SplitRequest import SplitRequest
from utils.helper.LineGraph import LineGraph, LineEdge
from utils.helper.PriorityQueue import PriorityQueue
from utils.network.Stop import Stop
from utils.network.Line import Line

AVERAGE_KMH: int
KM_PER_UNIT: int
COST_PER_KM: float
CO2_PER_KM: float
CAPACITY_PER_BUS: int
NUMBER_OF_EXTRA_TRANSFERS: int
MAX_DELAY_EQUATION: str
TRANSFER_MINUTES: int
TIME_WINDOW: int


def calc_distance(stop1: Stop, stop2: Stop) -> float:
    # calculate euclidean distance
    unit_dist = math.sqrt(
        (stop2.coordinates[0] - stop1.coordinates[0]) ** 2 + (stop2.coordinates[1] - stop1.coordinates[1]) ** 2)
    return unit_dist * KM_PER_UNIT


def calc_time(distance: float) -> float:
    return (distance * 60) / AVERAGE_KMH


# need to calculate number of transfers as well
def calc_fastest(pick_up_location: Stop, drop_off_location: Stop, network_graph: LineGraph):
    # dijkstra alg.
    pred_dict: Dict[Stop, (
        Set[Line], int)] = {}  # contains poss. lines request is in at stop v and number of transfers at this point
    for stop in network_graph.get_nodes():
        pred_dict[stop] = (set(), 0)

    pick_lines: frozenset = frozenset(
        [x for s in [line_set.lines for line_set in network_graph.get_edges_of_node(pick_up_location)] for x in s])
    pred_dict[pick_up_location] = (pick_lines, 1)

    queue: PriorityQueue = PriorityQueue(network_graph.get_nodes())
    queue.replace(pick_up_location, TRANSFER_MINUTES)

    while (not queue.is_empty()) and (queue.get_priority(drop_off_location) is not None):
        v, dist_v = queue.pop()
        for adj_edge in network_graph.get_edges_of_node(v):
            u = adj_edge.get_neighbour(v)
            dist_u = queue.get_priority(u)
            if dist_u is not None:
                # need to know in which lines u could be here -> if way to v is another line -> transfer time
                numb_transfer: int = pred_dict[v][1]
                alter: float = dist_v + adj_edge.duration
                intersect = adj_edge.lines & pred_dict[v][0]

                if len(intersect) == 0:
                    alter += TRANSFER_MINUTES
                    intersect = adj_edge.lines
                    numb_transfer += 1

                # if equal decide by number of transfers
                if alter < dist_u or (alter == dist_u and numb_transfer < pred_dict[u][1]):
                    queue.replace(u, alter)
                    pred_dict[u] = (intersect, numb_transfer)

    return queue.final_vals[drop_off_location], pred_dict[drop_off_location][1]


def complete_request(pick_up: Stop, drop_off: Stop, network_graph: LineGraph):
    # calculate fastest time -> account for transfers -> plug into max_delay_equation
    fastest_time, numb_transfers = calc_fastest(pick_up, drop_off, network_graph)
    long_delay = eval(MAX_DELAY_EQUATION, {"math": math, "x": fastest_time})

    return convert_2_time(long_delay + fastest_time + TIME_WINDOW), numb_transfers


# possible overflow here with time... have to consider this
def convert_2_time(duration_min: float):
    hours: int = math.floor(duration_min / 60)

    minutes: int = math.floor(duration_min) % 60
    if round(duration_min) > math.floor(duration_min):
        if minutes == 59:
            minutes = 0
            hours += 1
        else:
            minutes += 1

    if hours > 23:
        ValueError("time overflow occured")

    return time(hours, minutes)


def convert_2_minutes(time_object: time):
    sum_min: float = 0

    sum_min += 60 * time_object.hour
    sum_min += time_object.minute
    sum_min += time_object.second / 60

    return sum_min


def add_times(t1: time, t2: time):
    sum_sec: int = 0

    sum_sec += 3600 * (t1.hour + t2.hour)
    sum_sec += 60 * (t1.minute + t2.minute)
    sum_sec += t1.second + t2.second

    return convert_2_time(sum_sec / 60)


def sub_times(t1: time, t2: time):
    sum_sec = 0

    sum_sec += 3600 * (t1.hour - t2.hour)
    sum_sec += 60 * (t1.minute - t2.minute)
    sum_sec += t1.second - t2.second

    return convert_2_time(sum_sec / 60)


# check if hop-count exceeded -> add current stop to all open lists -> if not source: recursive call to neighbours
def rec_dfs(last_line: LineEdge, curr_minutes: float, curr_transfers: int, prev_visited: Set[Stop],
            curr_open: List[List[SplitRequest]], look_up_dict: Dict[LineEdge, SplitRequest], max_time: float,
            max_hop_count: int, target: Stop):
    if curr_transfers > max_hop_count or curr_minutes > max_time:
        return []
    else:
        for combi in curr_open:
            combi.append(look_up_dict[last_line])
        if last_line.v2 == target:
            return curr_open
        else:
            # find all successors of v2, that are not yet explored and operate on new line
            successors: List[LineEdge] = [x for x in look_up_dict.keys() if
                                          (x.v1 == last_line.v2) and (x.v2 not in prev_visited) and (
                                                      next(iter(x.lines)) != next(iter(last_line.lines)))]
            prev_visited.add(last_line.v1)

            combined_poss: List[List[SplitRequest]] = []
            for suc in successors:
                combined_poss += rec_dfs(suc, curr_minutes + TRANSFER_MINUTES + suc.duration, curr_transfers + 1,
                                         prev_visited.copy(), [x.copy() for x in curr_open], look_up_dict, max_time,
                                         max_hop_count, target)

            return combined_poss


def calc_time_multi(v1: Stop, v2: Stop, line: Line):
    index_v1: int = line.stops.index(v1)
    index_v2: int = line.stops.index(v2)

    # swap values if needed
    if index_v2 < index_v1:
        buf = index_v2
        index_v2 = index_v1
        index_v1 = buf

    duration: float = 0
    for i in range(index_v1, index_v2):
        duration += calc_time(calc_distance(line.stops[i], line.stops[i + 1]))

    return duration


# Algo to retrieve all possible Subroutes in network from transfer point to transfer point(call only once store in LineGraph?)
# + Per request: make SplitRequest for all pick-up/drop-off to transfer points subroutes(for every request) and for all subroutes in network -> store in dict

# only call dfs once with split-req dict, starting at all subroutes of start -> check time and transfer constraints
def find_split_requests(request: Request, network_graph: LineGraph) -> List[List[SplitRequest]]:
    # for pick-up and transfer point find all combis with transfer points

    pick_up_edges: List[LineEdge] = network_graph.get_edges_of_node(request.pick_up_location)
    drop_off_edges: List[LineEdge] = network_graph.get_edges_of_node(request.drop_off_location)

    pick_up_lines: Set[Line] = set.union(*[x.lines for x in pick_up_edges])
    drop_off_lines: Set[Line] = set.union(*[x.lines for x in drop_off_edges])

    pick_up_trans: Set[Stop] = set()
    # only need to look into further sub-lines if node is not a transfer point
    if len(pick_up_lines) == 1:
        # find all transfer points and store with in set
        line: Line = next(iter(pick_up_lines))
        for other in (network_graph.all_lines - {line}):
            pick_up_trans |= (set(line.stops) & set(other.stops))

    drop_off_trans: Set[Stop] = set()
    if len(drop_off_lines) == 1:
        # same for drop-off point
        line: Line = next(iter(drop_off_lines))
        # just check line against all other lines -> look for stops appearing mult. times
        for other in (network_graph.all_lines - {line}):
            drop_off_trans |= (set(line.stops) & set(other.stops))

    # fill dict of LineEdge to SplitRequest for all aggregated routes in network
    agg_edges_dict: Dict[LineEdge, SplitRequest] = {}
    for agg_edge in network_graph.aggregated_edges:
        agg_edges_dict[agg_edge] = SplitRequest(request.id, agg_edge.v1, agg_edge.v2, next(iter(agg_edge.lines)))

    # fill dict for pick-up to transfer points
    for trans_point in pick_up_trans:
        pick_up_line: Line = next(iter(pick_up_lines))
        duration: float = calc_time_multi(request.pick_up_location, trans_point, pick_up_line)
        agg_edges_dict[LineEdge(request.pick_up_location, trans_point, {pick_up_line}, duration)] = SplitRequest(
            request.id, request.pick_up_location, trans_point, pick_up_line)

    # fill dict for transfer point to drop-off
    for trans_point in drop_off_trans:
        drop_off_line: Line = next(iter(drop_off_lines))
        duration: float = calc_time_multi(trans_point, request.drop_off_location, drop_off_line)
        agg_edges_dict[LineEdge(trans_point, request.drop_off_location, {drop_off_line}, duration)] = SplitRequest(
            request.id, trans_point, request.drop_off_location, drop_off_line)

    # if at least one is not a transfer point
    if (len(pick_up_lines) == 1) and (len(drop_off_lines) == 1):
        combi_lines = pick_up_lines & drop_off_lines
        # if they are on the same line
        if len(combi_lines) > 0:
            line: Line = next(iter(combi_lines))
            duration: float = calc_time_multi(request.pick_up_location, request.drop_off_location, line)
            agg_edges_dict[
                LineEdge(request.pick_up_location, request.drop_off_location, {line}, duration)] = SplitRequest(
                request.id, request.pick_up_location, request.drop_off_location, line)

    # now do dfs with dictionary of split-requests, account for max. number of transfers and time constraints
    max_time: float = convert_2_minutes(request.latest_arr_time) - convert_2_minutes(request.earl_start_time) - 15

    # depth-first search to retrieve all combinations, starting at start-position
    result: List[List[SplitRequest]] = []
    start_tupels: List[LineEdge] = [x for x in agg_edges_dict.keys() if x.v1 == request.pick_up_location]

    for start_sub_line in start_tupels:
        result += rec_dfs(start_sub_line, TRANSFER_MINUTES + start_sub_line.duration, 1, {request.pick_up_location},
                          [[]], agg_edges_dict, max_time, request.numb_transfer + NUMBER_OF_EXTRA_TRANSFERS,
                          request.drop_off_location)

    return result
