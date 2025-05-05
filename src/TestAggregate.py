from pathlib import Path
from typing import Dict, List
import re

from matplotlib import pyplot as plt

from utils.helper import Timer
from utils.helper.Timer import TimeImpl


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

    if len(bus_files) > 0 and len(overall_file) > 0 and len(request_file) > 0:

        earl_time = TimeImpl(0, 0)
        latest_time = TimeImpl(23, 59)
        for b_name in bus_files:
            b_file = folder / b_name
            b_f = b_file.open("r", encoding="utf-8")
            b_lines = b_f.readlines()

            if len(b_lines) > 3:
                first_stop = b_lines[2]
                first_data = first_stop.split(",")
                start_time = Timer.conv_string_2_Time(first_data[2])
                if start_time < earl_time:
                    earl_time = start_time

                last_line = b_lines[-2]
                last_data = last_line.split(",")
                end_time = Timer.conv_string_2_Time(last_data[3])
                if end_time > latest_time:
                    latest_time = end_time
            b_f.close()

        duration_len = (latest_time - earl_time).get_in_minutes() / 60

        o_file = folder / overall_file[0]
        o_f = o_file.open("r", encoding="utf-8")
        o_lines = o_f.readlines()
        req_cell = [x for x in o_lines if "Number of Requests accepted:" in x]
        number_requests = int(req_cell[0].split(" ")[-1])

        density = number_requests / duration_len
        if density in val_dict:
            val_dict[density].append(o_lines)
        else:
            val_dict[density] = [o_lines]

        o_f.close()



# method receives path to folder root -> searches all subdirectories, looking for overall/request file -> extracts some value and makes plots
def aggregate_tests(folder_path: str):
    root_folder = Path(folder_path)
    val_dict = {}

    rec_check_folder(root_folder, val_dict)

    x = list()
    y = list()

    for key in val_dict.keys():
        for val in val_dict[key]:
            x.append(key)
            interesting_lines = [x for x in val if "system efficiency:" in x]
            if len(interesting_lines) == 0:
                print(val)
                raise ValueError("Important line not found")
            y.append(float(interesting_lines[0].split(" ")[-1]))

    plt.plot(x, y, 'ro')

    plt.savefig("C:\\Users\\jonas\\PycharmProjects\\liDARP\\output\\InterestingOutput\\aggFiles\\aggPlot.png")


aggregate_tests("C:\\Users\\jonas\\PycharmProjects\\liDARP\\output\\InterestingOutput")