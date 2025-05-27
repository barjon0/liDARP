from pathlib import Path
from typing import Dict, List
import re

from matplotlib import pyplot as plt

from utils.helper import Timer
from utils.helper.Timer import TimeImpl


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
        supposed_dur = int(parent_folder.name[1])

        return supposed_dur

def density_to_requests(parent_folder: Path, val_dict: dict, overall_lines: List[str], req_lines: List[str],
                          bus_names: List[str]):

    number_requests = len(req_lines) - 1

    density = number_requests / get_time_window_length(bus_names, parent_folder)
    req_cell = [x for x in overall_lines if "Number of Requests accepted:" in x]
    acc_req = int(req_cell[0].split(" ")[-1])
    if density in val_dict:
        val_dict[density].append(acc_req)
    else:
        val_dict[density] = [acc_req]

def density_to_efficiency(parent_folder: Path, val_dict: dict, overall_lines: List[str], req_lines: List[str],
                          bus_names: List[str]):
    req_cell = [x for x in overall_lines if "Number of Requests accepted:" in x]
    number_req = len(req_lines) - 1

    density = number_req / get_time_window_length(bus_names, parent_folder)
    interesting_lines = [x for x in overall_lines if "system efficiency:" in x]
    sys_eff = float(interesting_lines[0].split(" ")[-1])
    if density in val_dict:
        val_dict[density].append(sys_eff)
    else:
        val_dict[density] = [sys_eff]

def denied_req_density(parent_folder: Path, val_dict: dict, overall_lines: List[str], req_lines: List[str],
                          bus_names: List[str]):
    req_cell = [x for x in overall_lines if "Number of Requests accepted:" in x]
    number_req = len(req_lines) - 1
    number_denied_req = number_req - int(req_cell[0].split(" ")[-1])

    density = number_req / get_time_window_length(bus_names, parent_folder)
    if density in val_dict:
        val_dict[density].append(number_denied_req)
    else:
        val_dict[density] = [number_denied_req]


def density_computation_times(parent_folder: Path, val_dict: dict, overall_lines: List[str], req_lines: List[str], bus_names: List[str]):
    # req_cell = [x for x in overall_lines if "Number of Requests accepted:" in x]
    number_requests = len(req_lines) - 1

    density = number_requests / get_time_window_length(bus_names, parent_folder)

    interesting_lines = [x for x in overall_lines if "computation time" in x]
    comp_time = 0
    for t in interesting_lines:
        comp_time += Timer.conv_string_2_time(t.split(" ")[-1]).get_in_seconds()
    if True:
        if density in val_dict:
            val_dict[density].append(comp_time)
        else:
            val_dict[density] = [comp_time]

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

    density = number_requests / get_time_window_length(bus_names, parent_folder)

    interesting_lines = [x for x in overall_lines if "Event Graph Nodes:" in x]
    nNodes = int(interesting_lines[0].split(" ")[-1])

    if density in val_dict:
        val_dict[density].append(nNodes)
    else:
        val_dict[density] = [nNodes]


def rec_check_folder(folder: Path, val_dict: Dict[int, List[List[str]]]):
    files = list()
    for item in folder.iterdir():
        if item.is_dir():
            rec_check_folder(item, val_dict)
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

        denied_req_density(folder, val_dict, o_lines, r_lines, bus_files)


# method receives path to folder root -> searches all subdirectories, looking for overall/request file -> extracts some value and makes plots
def aggregate_tests(folder_path: str, figure, color_str: str):
    root_folder = Path(folder_path)
    val_dict = {}

    rec_check_folder(root_folder, val_dict)

    x = list()
    y = list()

    for key in val_dict.keys():
        for val in val_dict[key]:
            x.append(key)
            y.append(val)

    figure.plot(x, y, 'o', color=color_str, label=folder_path.split("/")[-1])

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
use_path = "../output/InterestingOutput/SingleObj"
start_folder = Path(use_path)
short_colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']
i = 0

for item in start_folder.iterdir():
    if item.is_dir():
        aggregate_tests(use_path + "/" + item.name, ax, short_colors[i])
        i += 1

#aggregate_tests("../output/InterestingOutput/SingleObj", ax, "blue")
#aggregate_tests("../output/InterestingOutput/MultiObj", ax, "red")

ax.set_title("Density to Denied Requests")
ax.set_xlabel("Density")
ax.set_ylabel("Number of Denied Requests")

ax.legend()
plt.savefig(find_output_path("../output/InterestingOutput/agg_plots"))
