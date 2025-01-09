import math
from datetime import time, timedelta
from typing import Dict, Set

from utils.demand.Request import Request
from utils.helper.LineGraph import LineGraph
from utils.helper.PriorityQueue import PriorityQueue
from utils.network import Stop
from utils.network.Line import Line

AVERAGE_KMH: int
KM_PER_UNIT: int
COST_PER_KM: float
CO2_PER_KM: float
CAPACITY_PER_BUS: int
NUMBER_OF_EXTRA_STOPS: int
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


def calc_fastest(pick_up_location, drop_off_location, network_graph):
    # dijkstra alg.
    pred_dict: Dict[Stop, Set[Line]] = {}
    for stop in network_graph.get_nodes():
        pred_dict[stop] = set()

    queue: PriorityQueue = PriorityQueue(network_graph.get_nodes())

    queue.replace(pick_up_location, 0)

    while (not queue.is_empty()) and (queue.get_priority(drop_off_location) is not None):
        v, dist_v = queue.pop()
        for adj_edge in network_graph.get_edges_of_node(v):
            u = adj_edge.get_neighbour(v)
            dist_u = queue.get_priority(u)
            if dist_u is not None:
                # need to know in which lines u could be here -> if way to v is another line -> transfer time
                alter: float = dist_v + adj_edge.duration
                intersect = adj_edge.lines & pred_dict[u]
                if len(intersect) == 0:
                    alter += TRANSFER_MINUTES

                # if equal decide by number of transfers(need to save this somewhere)
                if alter < dist_u:
                    queue.replace(u, alter)
                    pred_dict[u] = intersect

    return queue.final_vals[drop_off_location]


def calc_latest(pick_up: Stop, drop_off: Stop, network_graph: LineGraph):
    # calculate fastest time -> account for transfers -> plug into max_delay_equation
    fastest_time: float = calc_fastest(pick_up, drop_off, network_graph)
    long_delay = eval(MAX_DELAY_EQUATION, {"math": math, "x": fastest_time})

    return convert_2_time(long_delay + fastest_time + TIME_WINDOW)


# possible overflow here with time... have to consider this
def convert_2_time(duration: float):
    hours: int = math.floor(duration / 60)
    if hours > 23:
        ValueError("time overflow occured")
    minutes: int = math.floor(duration % 60)
    if (duration % 60) >= 30:
        minutes += 1

    return time(hours, minutes)


def add_times(t1: time, t2: time):
    sum_sec = 0

    sum_sec += 3600 * (t1.hour + t2.hour)
    sum_sec += 60 * (t1.minute + t2.minute)
    sum_sec += t1.second + t2.second

    return convert_2_time(sum_sec / 60)
