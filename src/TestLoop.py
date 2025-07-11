import os
import subprocess
import re
import sys

OUTPUT_PATH = "../output/InterestingOutput/liDARPT_4/"
def run_python_code(full_path, file_name):
    speed = None
    unitDist = None

    if "sw-geo" in full_path:
        speed = 70.0
        unitDist = 3.0
    elif "sw-schlee" in full_path:
        speed = 65.0
        unitDist = 1.5
    elif "markt-karl" in full_path:
        unitDist = 2.0
        speed = 65.0
    else:
        raise ValueError

    env = os.environ.copy()  # start with the current environment
    env["PYTHONPATH"] = "/HOME/s388381/liDARP/venv/lib/python3.10/site-packages"
    #env["CPLEX_STUDIO_DIR201"] = "/opt/ibm/ILOG/CPLEX_Studio201"
    network_name = re.split(r"[\\/]", full_path)[-3]
    length_word = re.split(r"[\\/]", full_path)[-2]
    output_path_all = os.path.join(str(OUTPUT_PATH), str(network_name), str(length_word))

    subprocess.run([sys.executable, "IOHandler.py", "../input/config.json", full_path, str(speed), str(unitDist), output_path_all], env=env)

def walk_and_run(directory):
    for root, dirs, files in os.walk(directory):
        for file_name in files:
            full_path = os.path.join(root, file_name)
            print("Found file: ", full_path)
            run_python_code(full_path, file_name)

walk_and_run(r"../input/requests/requests_5")
#walk_and_run(r"../input/requests/less_random_requests/sw-schlee_3")
