import csv
import json
import sys
from datetime import datetime, time
from typing import Set, List, Dict, Tuple

from main.plan.EventBasedMILP import EventBasedMILP
from main.plan.Planner import Planner
from main.scope.Context import Context, Static
from main.scope.Executor import Executor
from utils.demand.Request import Request
from utils.demand.SplitRequest import SplitRequest
from utils.helper import Helper
from utils.helper.LineGraph import LineGraph
from utils.network.Bus import Bus
from utils.network.Line import Line
from utils.network.Stop import Stop
from utils.plan.Route import Route


def find_planner(solver_str: str, network: List[Bus], network_graph: LineGraph):
    if solver_str == 'eventMILP':
        return EventBasedMILP(network, network_graph)
    else:
        raise ValueError("the given solver string is not registered in the system")


def find_context(context_str, requests: Set[Request], executor: Executor, planner: Planner):
    if context_str == 'static':
        return Static(requests, executor, planner)
    else:
        raise ValueError("the given context string is not registered in the system")


def read_requests(request_path, network_graph: LineGraph):
    request_set: Set[Request] = set()

    stops: Dict[int, Stop] = {}
    for stop in network_graph.get_nodes():
        stops[stop.id] = stop

    with open(request_path, 'r') as request_file:
        csv_requests = csv.reader(request_file)

        next(csv_requests)
        for row in csv_requests:
            earl_time: time = datetime.strptime(row[2], "%H:%M:%S").time()
            pick_up: Stop = stops[int(row[3])]
            drop_off: Stop = stops[int(row[4])]
            delay_time, numb_transfers = Helper.complete_request(pick_up, drop_off, network_graph)
            request_set.add(Request(int(row[0]), pick_up, drop_off,
                                    earl_time, Helper.add_times(earl_time, delay_time),
                                    datetime.strptime(row[1], "%H:%M:%S").time(), numb_transfers))

    return request_set


def read_bus_network(network_path: str):
    with open(network_path, 'r') as network_file:
        network_dict: dict = json.load(network_file)

    max_id: int = 0
    stops: Dict[int, Stop] = {}
    stop_list = network_dict.get('stops')
    for single_stop in stop_list:
        if single_stop["id"] > max_id:
            max_id = single_stop["id"]
        stops[single_stop["id"]] = Stop(single_stop["id"], tuple(single_stop["coordinates"]))

    lines: Dict[int, Line] = {}
    line_list = network_dict.get('lines')
    for line in line_list:
        stops_of_line: List[Stop] = []
        for stop_id in line["stops"]:
            stops_of_line.append(stops[stop_id])
        lines[line["id"]] = Line(line["id"], stops_of_line)

    busses: List[Bus] = []
    bus_list = network_dict.get('busses')
    depot_dict: Dict[Tuple[int, int], Stop] = {}

    for bus in bus_list:
        line_of_bus = lines[bus["line"]]

        depot_stop: Stop
        depot_coord: Tuple[int, int] = tuple(bus["depot"])
        if depot_coord in depot_dict:
            depot_stop = depot_dict[depot_coord]
        else:
            max_id = max_id + 1
            depot_stop = Stop(max_id, depot_coord)
            depot_dict[depot_coord] = depot_stop

        if Helper.CAPACITY_PER_BUS is None:
            busses.append(Bus(bus["id"], bus["capacity"], line_of_bus, depot_stop))
        else:
            busses.append(Bus(bus["id"], Helper.CAPACITY_PER_BUS, line_of_bus, depot_stop))

    return busses


def main(path_2_config: str):

    with open(path_2_config, 'r') as config_file:
        config: dict = json.load(config_file)

    Helper.AVERAGE_KMH = config.get('averageKmH')
    Helper.KM_PER_UNIT = config.get('KmPerUnit')
    Helper.COST_PER_KM = config.get('costPerKM')
    Helper.CO2_PER_KM = config.get('co2PerKM')
    Helper.CAPACITY_PER_BUS = config.get('capacityPerBus')
    Helper.NUMBER_OF_EXTRA_TRANSFERS = config.get('numberOfExtraTransfers')
    Helper.MAX_DELAY_EQUATION = config.get('maxDelayEquation')
    Helper.TRANSFER_MINUTES = config.get('transferMinutes')
    Helper.TIME_WINDOW = config.get('timeWindowMinutes')

    request_path: str = config.get('pathRequestFile')
    network_path: str = config.get('pathNetworkFile')
    context_str: str = config.get('context')
    solver_str: str = config.get('solver')

    network: List[Bus] = read_bus_network(network_path)
    network_graph = LineGraph(network)
    requests: Set[Request] = read_requests(request_path, network_graph)

    plann: Planner = find_planner(solver_str, network, network_graph)
    context: Context = find_context(context_str, requests, Executor(network), plann)

    for request in requests:
        split_lists: List[List[SplitRequest]] = Helper.find_split_requests(request, network_graph)
        for variation_numb in range(len(split_lists)):
            request.split_requests[variation_numb] = split_lists[variation_numb]

    context.start_context()


def create_output(requests: Set[Request], plan: Set[Route]):
    # for each bus create csv of stops(number, position, arriv_time, depart_time, pick_up_users, drop-off_users)
    # for each user create csv of (id, list of buses, waiting_time, ride_time)
    # system efficency = km booked(only direct km) / km travelled
    # deviation factor = accum km of each user / km booked
    # vehicle utilization = accum km of each user / km travelled (not empty)
    # empty km share = km empty / km travelled
    # (PoolingIndex = ??)
    # go through plan of each bus, add km to big numbers, fill requests finally, fill dict for bus csv
    pass


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # The first argument is the file path
        config_path = sys.argv[1]
        main(config_path)
    else:
        print("Please provide the file path to the config file as an argument.")
