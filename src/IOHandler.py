import csv
import json
import sys
import os
from typing import Set, List, Dict, Tuple

import Global
from main.plan.EventBasedMILP import EventBasedMILP
from main.plan.Planner import Planner
from main.scope.Context import Context, Static
from main.scope.Executor import Executor
from utils.demand.Request import Request
from utils.demand.SplitRequest import SplitRequest
from utils.helper import Helper, Timer
from utils.helper.LineGraph import LineGraph
from utils.helper.Timer import TimeImpl
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
    for stop in network_graph.all_stops:
        stops[stop.id] = stop

    with open(request_path, 'r') as request_file:
        csv_requests = csv.reader(request_file)

        next(csv_requests)
        for row in csv_requests:
            earl_time = Timer.conv_string_2_Time(row[2])
            pick_up: Stop = stops[int(row[3])]
            drop_off: Stop = stops[int(row[4])]
            req_id: int = int(row[0])

            network_graph.add_request(pick_up, drop_off)

            print(req_id)
            delay_time, numb_transfers, km_planned = Helper.complete_request(pick_up, drop_off, network_graph, int(row[5]))
            request = Request(int(row[0]), int(row[5]), pick_up, drop_off,
                              earl_time, earl_time + delay_time,
                              Timer.conv_string_2_Time(row[1]), numb_transfers, km_planned)

            split_lists: List[List[SplitRequest]] = Helper.find_split_requests(request, network_graph)
            for variation_numb in range(len(split_lists)):
                request.split_requests[variation_numb] = split_lists[variation_numb]
                fill_time_windows(request, split_lists[variation_numb])

            network_graph.delete_request(pick_up, drop_off)

            request_set.add(request)

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
    depot_dict: Dict[Tuple[int, int], Stop] = {}
    for line in line_list:
        depot_stop: Stop
        depot_coord: Tuple[int, int] = tuple(line["depot"])

        if depot_coord in depot_dict:
            depot_stop = depot_dict[depot_coord]
        else:
            max_id = max_id + 1
            depot_stop = Stop(max_id, depot_coord)
            depot_dict[depot_coord] = depot_stop

        stops_of_line: List[Stop] = []
        for stop_id in line["stops"]:
            stops_of_line.append(stops[stop_id])
        if Global.CAPACITY_PER_LINE is None:
            if "capacity" in line:
                lines[line["id"]] = Line(line["id"], stops_of_line, depot_stop, int(line["capacity"]), Timer.conv_string_2_Time(line["startTime"]), Timer.conv_string_2_Time(line["endTime"]))
            else:
                ValueError("No Global Capacity or individual given")
        else:
            lines[line["id"]] = Line(line["id"], stops_of_line, depot_stop, Global.CAPACITY_PER_LINE, Timer.conv_string_2_Time(line["startTime"]), Timer.conv_string_2_Time(line["endTime"]))

    busses: List[Bus] = []
    bus_list = network_dict.get('busses')

    for bus in bus_list:
        busses.append(Bus(bus["id"], lines[bus["line"]]))

    return busses


def fill_time_windows(request: Request, split_req_list: List[SplitRequest]):
    # go through split_req_list and fill time windows (as big as possible)
    total_distance: float = sum(Helper.calc_distance(x.pick_up_location, x.drop_off_location) for x in split_req_list)

    shortest_time: float = Timer.calc_time(total_distance) + (len(split_req_list) * Global.TRANSFER_MINUTES)
    curr_earl_time: float = 0

    # special case for first split, because of fixed time window for pick-up
    start_split = split_req_list[0]
    start_split.earl_start_time = request.earl_start_time
    start_split.latest_start_time = request.earl_start_time.add_minutes(Global.TIME_WINDOW)

    curr_earl_time += Global.TRANSFER_MINUTES + Timer.calc_time(
        Helper.calc_distance(start_split.pick_up_location, start_split.drop_off_location))

    start_split.earl_arr_time = start_split.earl_start_time.add_minutes(curr_earl_time)
    prop_lat_arr = request.latest_arr_time.sub_minutes(shortest_time - curr_earl_time)
    if start_split.latest_arr_time is None or start_split.latest_start_time < prop_lat_arr:
        start_split.latest_arr_time = prop_lat_arr

    assert start_split.earl_arr_time < start_split.latest_arr_time

    for split_req in split_req_list[1:]:
        prop_time_earl_start = request.earl_start_time.add_minutes(curr_earl_time)
        if split_req.earl_start_time is None or split_req.earl_start_time > prop_time_earl_start:
            split_req.earl_start_time = prop_time_earl_start

        intermediate_time = Global.TRANSFER_MINUTES + Timer.calc_time(
            Helper.calc_distance(split_req.pick_up_location, split_req.drop_off_location))

        prop_time_earl_arr = prop_time_earl_start.add_minutes(intermediate_time)
        if split_req.earl_arr_time is None or split_req.earl_arr_time > prop_time_earl_arr:
            split_req.earl_arr_time = prop_time_earl_arr

        curr_earl_time += intermediate_time
        prop_time_lat_arr = request.latest_arr_time.sub_minutes(shortest_time - curr_earl_time)
        if split_req.latest_arr_time is None or split_req.latest_arr_time < prop_time_lat_arr:
            split_req.latest_arr_time = prop_time_lat_arr

        prop_time_lat_start = prop_time_lat_arr.sub_minutes(intermediate_time)
        if split_req.latest_start_time is None or split_req.latest_start_time < prop_time_lat_start:
            split_req.latest_start_time = prop_time_lat_start


def main(path_2_config: str):
    with open(path_2_config, 'r') as config_file:
        config: dict = json.load(config_file)

    Global.AVERAGE_KMH = config.get('averageKmH')
    Global.KM_PER_UNIT = config.get('KmPerUnit')
    Global.COST_PER_KM = config.get('costPerKM')
    Global.CO2_PER_KM = config.get('co2PerKM')
    Global.CAPACITY_PER_LINE = config.get('capacityPerLine')
    Global.NUMBER_OF_EXTRA_TRANSFERS = config.get('numberOfExtraTransfers')
    Global.MAX_DELAY_EQUATION = config.get('maxDelayEquation')
    Global.TRANSFER_MINUTES = config.get('transferMinutes')
    Global.TIME_WINDOW = config.get('timeWindowMinutes')
    Global.CPLEX_PATH = config.get('pathCPLEX')

    request_path: str = config.get('pathRequestFile')
    network_path: str = config.get('pathNetworkFile')
    output_path: str = config.get('outputPath')
    context_str: str = config.get('context')
    solver_str: str = config.get('solver')

    network: List[Bus] = read_bus_network(network_path)
    network_graph = LineGraph(network)
    requests: Set[Request] = read_requests(request_path, network_graph)

    plann: Planner = find_planner(solver_str, network, network_graph)
    context: Context = find_context(context_str, requests, Executor(network, requests), plann)

    context.start_context()

    create_output(requests, context.executor.routes, output_path)


def find_output_path(base_output_path: str):
    max_number = 0
    subdirectories = [name for name in os.listdir(base_output_path)
                      if os.path.isdir(os.path.join(base_output_path, name))]

    for sub_name in subdirectories:
        split_name = sub_name.split("_")
        index: int
        try:
            index = int(split_name[-1])
            if max_number < index:
                max_number = index
        except ValueError:
            pass

    result_path = f"{base_output_path}/run_{max_number + 1}"
    os.makedirs(result_path)

    return result_path


def create_output(requests: Set[Request], plans: Set[Route], base_output_path: str):
    # for each bus create csv of stops(number, position, arriv_time, depart_time, pick_up_users, drop-off_users)
    # for each user create csv of (id, list of buses, list of transfer points, waiting_time, ride_time)
    # system efficency = km booked(only direct km) / km travelled
    # deviation factor = accum km of each user / km booked
    # vehicle utilization = accum km of each user / km travelled (not empty)
    # empty km share = km empty / km travelled
    # (PoolingIndex = ??)
    # go through plan of each bus, add km to big numbers, fill requests finally, fill dict for bus csv

    buses = [x.bus for x in plans]

    numb_denied = 0
    km_booked = 0
    bus_overall_km_dict: Dict[Bus, float] = dict.fromkeys(buses, 0)
    bus_empty_km_dict: Dict[Bus, float] = dict.fromkeys(buses, 0)
    req_km_dict: Dict[Request, float] = dict.fromkeys(requests, 0)
    request_stop_dict: Dict[Request, List[int]] = {}
    request_wait_time_dict: Dict[Request, TimeImpl] = {}
    request_buses_dict: Dict[Request, List[int]] = {x: [] for x in requests}

    csv_out_bus: Dict[Bus, List[List[str]]] = {
        x: [["number", "stop ID", "arrival time", "departure time", "pick up users", "drop of users"]] for x in
        buses}
    csv_out_req: List[List[str]] = [["user ID", "used buses", "used transfer points", "waiting time", "ride time"]]

    for req in requests:
        if req.act_start_time is not None:
            km_booked += req.km_planned
            request_stop_dict[req] = [req.pick_up_location.id]
        else:
            numb_denied += 1

    for plan in plans:
        if len(plan.stop_list) > 0:
            prev_event = plan.stop_list[0]
            passengers: Set[Request] = set(prev_event.pick_up)
            bus_overall_km_dict[plan.bus] = 0
            csv_out_bus[plan.bus].append([1] + prev_event.to_output())
            counter = 2

            for curr_stop in plan.stop_list[1:]:
                csv_out_bus[plan.bus].append([counter] + curr_stop.to_output())
                km_between = Helper.calc_distance(prev_event.stop, curr_stop.stop)
                bus_overall_km_dict[plan.bus] += km_between
                if len(passengers) == 0:
                    bus_empty_km_dict[plan.bus] += km_between
                else:
                    for user in passengers:
                        req_km_dict[user] += km_between

                for u_dropped in curr_stop.drop_off:
                    request_stop_dict[u_dropped].append(curr_stop.stop.id)
                    request_buses_dict[u_dropped].append(curr_stop.bus.id)

                passengers = (passengers - curr_stop.drop_off) | curr_stop.pick_up
                counter += 1

    for req in requests:
        if req.act_start_time is not None:
            request_wait_time_dict[req] = (req.act_end_time - req.act_start_time).sub_minutes(
                Timer.calc_time(req_km_dict[req]))
            csv_out_req.append(
                [str(req), str(request_buses_dict[req]), str(request_stop_dict[req]),
                 str(request_wait_time_dict[req]), Timer.calc_time(req_km_dict[req])])
        else:
            csv_out_req.append([str(req), "-", "-", "-", "-"])

    overall_numbers: List[List[str]] = []
    km_travel_total = sum(bus_overall_km_dict.values())
    km_empty_total = sum(bus_empty_km_dict.values())
    km_used_total = km_travel_total - km_empty_total
    overall_numbers += [[f"km travelled total: {km_travel_total}"], [f"empty km total: {km_empty_total}"],
                        [f"used km total: {km_used_total}"]]

    acc_km_req = sum(req_km_dict.values())

    try:
        overall_numbers.append([f"system efficiency: {km_booked / km_travel_total}"])
        overall_numbers.append([f"deviation factor: {acc_km_req / km_booked}"])
        overall_numbers.append([f"vehicle utilization: {acc_km_req / km_used_total}"])
        overall_numbers.append([f"empty km share: {km_empty_total / km_travel_total}"])
    except ZeroDivisionError:
        pass

    path_to_output = find_output_path(base_output_path)

    for bus in buses:
        with open(f"{path_to_output}/bus_{bus.id}_out.csv", mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(csv_out_bus[bus])

    with open(f"{path_to_output}/requests_out.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerows(csv_out_req)

    with open(f"{path_to_output}/overall_out.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerows(overall_numbers)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # The first argument is the file path
        config_path = sys.argv[1]
        main(config_path)
    else:
        print("Please provide the file path to the config file as an argument.")
