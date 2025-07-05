import json
import math
from pathlib import Path
from platform import system
from typing import Dict, List
import re

from matplotlib import pyplot as plt

from utils.helper import Timer, Helper
from utils.helper.Timer import TimeImpl
from utils.network.Bus import Bus
from utils.network.Stop import Stop

translate_km = {"markt-karl": 2, "markt-karl-lohr": 2, "sw-geo_2": 3, "sw-geo_full": 3, "sw-schlee_2": 1.5, "sw-schlee_3": 1.5, "sw-schlee_full": 1.5}
translate_time = {"markt-karl": 65.0, "markt-karl-lohr": 65.0, "sw-geo_2": 70.0, "sw-geo_full": 70.0, "sw-schlee_2": 65.0, "sw-schlee_3": 65.0, "sw-schlee_full": 65.0}


def add_to_dict(network_name, number_requests, time_span, comp_time, val_dict):
    if network_name in val_dict:
        if (number_requests, time_span) in val_dict[network_name]:
            val_dict[network_name][(number_requests, time_span)] += [comp_time]
        else:
            val_dict[network_name][(number_requests, time_span)] = [comp_time]
    else:
        val_dict[network_name] = {(number_requests, time_span): [comp_time]}

def calc_dist(stop1, stop2, un):
    unit_dist = math.sqrt(
        (stop2.coordinates[0] - stop1.coordinates[0]) ** 2 + (stop2.coordinates[1] - stop1.coordinates[1]) ** 2)
    return unit_dist * un

def read_Length(network_name: str):
    network_path = "../input/bus_networks/real_networks/"
    network_file_path = network_path + network_name + ".json"
    with open(network_file_path, 'r') as network_file:
        network_dict: dict = json.load(network_file)

    stops: Dict[int, Stop] = {}
    stop_list = network_dict.get('stops')
    for single_stop in stop_list:
        stops[single_stop["id"]] = Stop(single_stop["id"], tuple(single_stop["coordinates"]))

    length = 0
    line_list = network_dict.get('lines')
    for line in line_list:
        stops_l = line["stops"]
        for i in range(len(stops_l)-1):
            length += calc_dist(stops[stops_l[i]], stops[stops_l[i+1]], translate_km[network_name])

    return length


def calculate_km_booked_instance(network_name: str, req_file_lines: List[str]):
    network_path = "../input/bus_networks/real_networks/"
    network_file_path = network_path + network_name + ".json"
    with open(network_file_path, 'r') as network_file:
        network_dict: dict = json.load(network_file)

    stops: Dict[int, Stop] = {}
    stop_list = network_dict.get('stops')
    for single_stop in stop_list:
        stops[single_stop["id"]] = Stop(single_stop["id"], tuple(single_stop["coordinates"]))

    km_booked = 0
    for req_line in req_file_lines[1:]:
        # Split by commas not inside brackets or quotes
        idx_1 = req_line.rfind("[")
        idx_2 = req_line.rfind("]")
        if idx_1 != -1:
            enc = req_line[idx_1 + 1:idx_2].split(", ")
            km_booked += calc_dist(stops[int(enc[0])], stops[int(enc[-1])], translate_km[network_name])

    return km_booked

def average_delay(parent_folder: Path, val_dict: dict, overall_lines: List[str], req_lines: List[str],
                          bus_names: List[str]):
    network_name = str(parent_folder).split("\\")[-3]
    time_span = float(parent_folder.name[1])
    number_req = len(req_lines) - 1

    avg_delay = 0
    i = 0
    for r_line in req_lines[1:]:
        buf = r_line.split(",")
        ride_time = buf[-3]
        if ride_time != "-":
            i += 1
            avg_delay += float(ride_time)

    int_line = [x for x in overall_lines if "km travelled total:" in x]
    use_km = float(get_val(int_line))
    use_dur = 60 * use_km / translate_time[network_name]

    add_to_dict(network_name, number_req, time_span, avg_delay / use_dur, val_dict)

def get_time_window_length(bus_files: List[str], parent_folder: Path):
    if len(bus_files) > 0:

        earl_time = TimeImpl(23, 59)
        latest_time = TimeImpl(0, 0)
        for b_name in bus_files:
            b_file = parent_folder / b_name
            b_f = b_file.open("r", encoding="utf-8")
            b_lines = b_f.readlines()

            if len(b_lines) > 3:
                first_stop = b_lines[3]
                first_data = first_stop.split(",")
                start_time = Timer.conv_string_2_time(first_data[2])
                if start_time < earl_time:
                    earl_time = start_time

                last_line = b_lines[-2]
                last_data = last_line.split(",")
                end_time = Timer.conv_string_2_time(last_data[3])
                if end_time > latest_time:
                    latest_time = end_time
            b_f.close()

        duration =  (latest_time - earl_time).get_in_seconds() / 3600

        return duration

def requests_to_efficiency(parent_folder: Path, val_dict: dict, overall_lines: List[str], req_lines: List[str],
                          bus_names: List[str]):
    network_name = str(parent_folder).split("\\")[-3]
    time_span = float(parent_folder.name[1])
    number_req = len(req_lines) - 1
    '''
    empty_line = [x for x in overall_lines if "empty km total:" in x]
    empty_km = float(empty_line[0].split(" ")[-1])
    total_line = [x for x in overall_lines if "km travelled total:" in x]
    total_km = float(total_line[0].split(" ")[-1])
    share = empty_km / total_km
    '''
    interesting_lines = [x for x in overall_lines if "computation time" in x]
    comp_time = 0
    for t in interesting_lines[3:]:
        comp_time += Timer.conv_string_2_time(t.split(" ")[-1]).get_in_seconds()
    #length = read_Length(network_name)
    interesting_lines2 = [x for x in overall_lines if "system efficiency:" in x]
    val2 = float(interesting_lines2[0].split(" ")[-1])
    #interesting_lines = [x for x in overall_lines if "Number of Requests accepted:" in x]
    #val = float(interesting_lines[0].split(" ")[-1])
    #km_booked = calculate_km_booked_instance(network_name, req_lines)
    #acc_req = val * 100 / number_req
    #if val2 == 0.0:
    #print(f"Denied in %: {acc_req}; Mip GAp:  {val2}; network: {network_name}; req: {number_req}")
    add_to_dict(network_name, number_req, time_span, val2, val_dict)


def event_graph_to_comp_time(parent_folder: Path, val_dict: dict, overall_lines: List[str], req_lines: List[str], bus_names: List[str]):
    network_name = str(parent_folder).split("\\")[-3]
    interesting_lines = [x for x in overall_lines if "Event Graph Nodes:" in x]
    nNodes = int(interesting_lines[0].split(" ")[-1])

    int_line2 = [x for x in overall_lines if "Event Graph Edges:" in x]
    edges = int(int_line2[0].split(" ")[-1])

    interesting_lines = [x for x in overall_lines if "computation time" in x]
    comp_time = 0
    for t in interesting_lines:
        comp_time += Timer.conv_string_2_time(t.split(" ")[-1]).get_in_seconds()

    add_to_dict(network_name, nNodes, edges, [nNodes, edges, comp_time], val_dict)

def get_val(line: List[str]):
    return line[0].split(" ")[-1]

def read_DARP(parent_folder: Path, val_dict: dict, overall_lines: List[str], file_name: str):
    sys_eff_line = [x for x in overall_lines if "System efficiency" in x]
    network_name = str(parent_folder).split("\\")[-2]
    time_span = float(file_name[1])
    number_req_line = [x for x in overall_lines if "Number of requests" in x]
    number_req = float(number_req_line[0].split(" ")[-1])

    if "-nan" not in get_val(sys_eff_line):
        interest_line_1 = [x for x in overall_lines if "System efficiency" in x]
        val = float(interest_line_1[0].split(" ")[-1])

        interest_line_2 = [x for x in overall_lines if "EntireModel time (ms)" in x]
        val_2 = float(interest_line_2[0].split(" ")[-1]) / 1000.0

        #per = (number_req - val_2) * 100 / float(number_req)
        #sys_eff = float(get_val(sys_eff_line)[0:-2])
        #if val < 0.2:
        add_to_dict(network_name, number_req, time_span, val_2, val_dict)
    else:
        print(f"network name {network_name}; numb_req: {number_req}; time_span: {time_span}")


def rec_check_folder(folder: Path, val_dict: Dict[str, Dict[int, List[float]]], duration: int):
    files = list()
    for item in folder.iterdir():
        if item.is_dir():
            rec_check_folder(item, val_dict, duration)
        if item.is_file():
            files.append(item.name)

    bus_files = [x for x in files if re.match("bus_.*", x)]
    overall_file = [x for x in files if x == "overall_out.csv"]
    request_file = [x for x in files if x == "requests_out.csv"]

    if len(overall_file) > 0:
        o_file = folder / overall_file[0]
        o_f = o_file.open("r", encoding="utf-8")
        o_lines = o_f.readlines()
        o_f.close()

        r_file = folder / request_file[0]
        r_f = r_file.open("r", encoding="utf-8")
        r_lines = r_f.readlines()
        r_f.close()

        if duration is None or int(folder.name[1]) == duration:
            event_graph_to_comp_time(folder, val_dict, o_lines, r_lines, bus_files)

def rec_check_folder_DARP(parent_folder, val_dict, duration):
    files = list()
    for item in parent_folder.iterdir():
        if item.is_dir():
            rec_check_folder_DARP(item, val_dict, duration)
        if item.is_file():
            files.append(item.name)

    for file in files:
        o_file = parent_folder / file
        o_f = o_file.open("r", encoding="utf-8")
        o_lines = o_f.readlines()
        o_f.close()

        if duration is None or int(file[1]) == duration:
            read_DARP(parent_folder, val_dict, o_lines, file)

# method receives path to folder root -> searches all subdirectories, looking for overall/request file -> extracts some value and makes plots
def aggregate_tests(folder_path: str, figure, duration: int=None):
    root_folder = Path(folder_path)
    val_dict = {}

    rec_check_folder(root_folder, val_dict, duration)
    #rec_check_folder_DARP(root_folder, val_dict, duration)

    '''    
    # val_dict = [(nodes, edges): [seconds]]
    x = list()
    y = list()
    z = list()
    for key in val_dict:
        for tup in val_dict[key].keys():
            x.append(tup[0])
            y.append(tup[1])
            z.append(val_dict[key][tup][0])

    sc = ax.scatter(x, y, c=z, cmap='viridis')
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("Seconds")
    '''

    short_colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']
    i = 0
    n = 0
    sumAll = 0
    x = list()
    y = list()
    z = list()
    n_list = sorted(list(val_dict.keys()))
    for key in n_list:
        key_list = sorted(list(val_dict[key].keys()), key=lambda x: x[0])
        for val in key_list:
            #if val_dict[key][val][0] > sumAll:
            #    sumAll = val_dict[key][val][0]
            x.append(val_dict[key][val][0][0])
            y.append(val_dict[key][val][0][1])
            z.append(val_dict[key][val][0][2])
    sc = ax.scatter(x, y, c=z, cmap='viridis')
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label('seconds')
    #print("number instances: " + str(sumAll))

# method receives path to folder root -> searches all subdirectories, looking for overall/request file -> extracts some value and makes plots
def aggregate_difference(folder_path_1: str, folder_path_DARP: str, figure, duration: int = None):
    root_folder_1 = Path(folder_path_1)
    val_dict = {}

    rec_check_folder(root_folder_1, val_dict, duration)

    root_folder_DARP = Path(folder_path_DARP)
    rec_check_folder_DARP(root_folder_DARP, val_dict, duration)
    #rec_check_folder(root_folder_DARP, val_dict, duration)

    short_colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']
    i = 0

    # val_dict:[network_name, [number requests, List[value]]]
    n_list = sorted(list(val_dict.keys()))
    n = 0
    sumVal = 0
    count = 0
    for network in n_list:
        x = list()
        y = list()
        #request_numbers = sorted(list(val_dict[network].keys()))
        for tup in val_dict[network].keys():
            if len(val_dict[network][tup]) == 2:
                dens = tup[0] / tup[1]
                val = val_dict[network][tup][1] - val_dict[network][tup][0]
                n += 1
                if val <= -1:
                    count += 1
                    sumVal += val
                x.append(dens)
                y.append(val)
        figure.plot(x, y, 'o', color=short_colors[i], label=network)
        i += 1
    print("all number " + str(n))
    print("counted: " + str(count))
    print("sumVal: " + str(sumVal))

def find_output_path(base_output_path: str):
    max_number = 0
    out_folder = Path(base_output_path)
    for item in out_folder.iterdir():
        if item.is_file() and "agg_plots_" in item.name:
            index = int(item.name.split(".")[0].split("_")[-1])
            if index > max_number:
                max_number = index

    result_path = f"{base_output_path}/agg_plots_{max_number + 1}.pdf"

    return result_path



fig, ax = plt.subplots()
#ax.set_ylim(-0.1, 1.5)
#use_path = "../output/InterestingOutput/SingleObj"
#start_folder = Path(use_path)

#i = 0
'''
for item in start_folder.iterdir():
    if item.is_dir():
        aggregate_tests(use_path + "/" + item.name, ax, short_colors[i])
        i += 1
'''

#ax.axhline(y=1.0, color='gray', linestyle='--', linewidth=1)
ax.set_yscale('log')
ax.set_xscale('log')
#ax.yaxis.set_major_formatter(ScalarFormatter())
#ax.yaxis.set_minor_formatter(ScalarFormatter())

#aggregate_difference("../output/InterestingOutput/SingleObj", "../output/InterestingOutput/DARP_0", ax, None)
aggregate_tests("../output/InterestingOutput/SingleObj", ax, None)

ax.set_title("Event Graph Size to Computation Time")
#ax.set_xlabel("Density (Requests / time span length)")
ax.set_xlabel("Number of Nodes")
ax.set_ylabel("Number of Edges")

#ax.legend()
plt.savefig(find_output_path("../output/InterestingOutput/agg_plots"), bbox_inches='tight')
