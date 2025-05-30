from pathlib import Path
from typing import Dict, List
import re

from matplotlib import pyplot as plt
from matplotlib.ticker import ScalarFormatter

from utils.helper import Timer
from utils.helper.Timer import TimeImpl


def add_to_dict(network_name, number_requests, comp_time, val_dict):
    if network_name in val_dict:
        if number_requests in val_dict[network_name]:
            val_dict[network_name][number_requests] += [comp_time]
        else:
            val_dict[network_name][number_requests] = [comp_time]
    else:
        val_dict[network_name] = {number_requests: [comp_time]}

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

def density_to_requests(parent_folder: Path, val_dict: dict, overall_lines: List[str], req_lines: List[str],
                          bus_names: List[str]):

    number_requests = len(req_lines) - 1

    density = number_requests / float(parent_folder.name[1])
    req_cell = [x for x in overall_lines if "Number of Requests accepted:" in x]
    acc_req = int(req_cell[0].split(" ")[-1])
    if density in val_dict:
        val_dict[density].append(acc_req)
    else:
        val_dict[density] = [acc_req]

def requests_to_efficiency(parent_folder: Path, val_dict: dict, overall_lines: List[str], req_lines: List[str],
                          bus_names: List[str]):
    req_cell = [x for x in overall_lines if "Number of Requests accepted:" in x]
    number_req = len(req_lines) - 1

    network_name = str(parent_folder).split("/")[-3]

    interesting_lines = [x for x in overall_lines if "system efficiency:" in x]
    sys_eff = float(interesting_lines[0].split(" ")[-1])
    add_to_dict(network_name, number_req, sys_eff, val_dict)

def acc_requests_req(parent_folder: Path, val_dict: dict, overall_lines: List[str], req_lines: List[str],
                          bus_names: List[str]):
    network_name = str(parent_folder).split("/")[-3]
    req_cell = [x for x in overall_lines if "Number of Requests accepted:" in x]
    number_req = len(req_lines) - 1
    acc_req = int(req_cell[0].split(" ")[-1])

    add_to_dict(network_name, number_req, acc_req, val_dict)


def req_computation_times(parent_folder: Path, val_dict: dict, overall_lines: List[str], req_lines: List[str], bus_names: List[str]):
    # req_cell = [x for x in overall_lines if "Number of Requests accepted:" in x]
    network_name = str(parent_folder).split("/")[-3]
    number_requests = len(req_lines) - 1

    interesting_lines = [x for x in overall_lines if "computation time" in x]
    comp_time = 0
    for t in interesting_lines:
        comp_time += Timer.conv_string_2_time(t.split(" ")[-1]).get_in_seconds()
    if True:
        add_to_dict(network_name, number_requests, comp_time, val_dict)

def event_graph_to_comp_time(parent_folder: Path, val_dict: dict, overall_lines: List[str], req_lines: List[str], bus_names: List[str]):
    interesting_lines = [x for x in overall_lines if "Event Graph Nodes:" in x]
    nNodes = int(interesting_lines[0].split(" ")[-1])

    interesting_lines = [x for x in overall_lines if "computation time" in x]
    comp_time = 0
    for t in interesting_lines:
        comp_time += Timer.conv_string_2_time(t.split(" ")[-1]).get_in_seconds()
    if True:
        if nNodes in val_dict:
            val_dict[nNodes].append(comp_time)
        else:
            val_dict[nNodes] = [comp_time]


def density_event_nodes(parent_folder: Path, val_dict: dict, overall_lines: List[str], req_lines: List[str], bus_names: List[str]):
    # req_cell = [x for x in overall_lines if "Number of Requests accepted:" in x]
    number_requests = len(req_lines) - 1

    density = number_requests / float(parent_folder.name[1])

    interesting_lines = [x for x in overall_lines if "Event Graph Nodes:" in x]
    nNodes = int(interesting_lines[0].split(" ")[-1])

    if density in val_dict:
        val_dict[density].append(nNodes)
    else:
        val_dict[density] = [nNodes]


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
            acc_requests_req(folder, val_dict, o_lines, r_lines, bus_files)


# method receives path to folder root -> searches all subdirectories, looking for overall/request file -> extracts some value and makes plots
def aggregate_tests(folder_path: str, figure, color_str: str, duration: int=None):
    root_folder = Path(folder_path)
    val_dict = {}

    rec_check_folder(root_folder, val_dict, duration)

    x = list()
    y = list()

    for key in val_dict.keys():
        for val in val_dict[key]:
            x.append(key)
            y.append(val)

    figure.plot(x, y, 'o', color=color_str, label=folder_path.split("/")[-1])

# method receives path to folder root -> searches all subdirectories, looking for overall/request file -> extracts some value and makes plots
def aggregate_difference(folder_path_1: str, folder_path_2: str, figure, duration: int = None):
    root_folder_1 = Path(folder_path_1)
    val_dict = {}

    rec_check_folder(root_folder_1, val_dict, duration)

    root_folder_2 = Path(folder_path_2)
    rec_check_folder(root_folder_2, val_dict, duration)

    short_colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']
    i = 0

    # val_dict:[network_name, [number requests, List[value]]]
    for network in val_dict.keys():
        x = list()
        y = list()
        for numbRequests in val_dict[network].keys():
            x.append(numbRequests)
            y.append(val_dict[network][numbRequests][1] - val_dict[network][numbRequests][0])
        figure.plot(x, y, 'o', color=short_colors[i], label=network)
        i += 1

def find_output_path(base_output_path: str):
    max_number = 0
    out_folder = Path(base_output_path)
    for item in out_folder.iterdir():
        if item.is_file() and "agg_plots_" in item.name:
            index = int(item.name.split(".")[0].split("_")[-1])
            if index > max_number:
                max_number = index

    result_path = f"{base_output_path}/agg_plots_{max_number + 1}.png"

    return result_path



fig, ax = plt.subplots()
#use_path = "../output/InterestingOutput/SingleObj"
#start_folder = Path(use_path)

#i = 0
'''
for item in start_folder.iterdir():
    if item.is_dir():
        aggregate_tests(use_path + "/" + item.name, ax, short_colors[i])
        i += 1
'''

ax.axhline(y=0.0, color='gray', linestyle='--', linewidth=1)
#ax.set_yscale('log')
#ax.yaxis.set_major_formatter(ScalarFormatter())
#ax.yaxis.set_minor_formatter(ScalarFormatter())

aggregate_difference("../output/InterestingOutput/MultiObj", "../output/InterestingOutput/SingleObj", ax,3)


ax.set_title("Difference in Accepted Requests - 3 hours length")
ax.set_xlabel("Number Requests")
ax.set_ylabel("Difference Accepted Requests(Single - Multi)")

ax.legend()
plt.savefig(find_output_path("../output/InterestingOutput/agg_plots"))
