import os
import subprocess

# Path to the root folder to search
ROOT_DIR = '/HOME/s388381/tight_formulation/a-tight-formulation-for-the-darp/data/my_data_kinda'
OUTPUT_PATH = "/HOME/s388381/tight_formulation/a-tight-formulation-for-the-darp/DARP_new_4/"

# Path to compiled C-code executable (e.g., "./my_program" or "C:\\path\\to\\program.exe")
C_EXECUTABLE = '/HOME/s388381/tight_formulation/a-tight-formulation-for-the-darp/bin/darpbc'

def run_c_code(folder_path, file_name):
    """Run the C executable, optionally passing the folder path as an argument."""

    speed = None
    length = None
    if "markt-karl" in folder_path:
        speed = 65.0
        length = 110.0
    elif "markt-karl-lohr" in folder_path:
        speed = 65.0
        length = 166.0
    elif "sw-geo_2" in folder_path:
        speed = 70.0
        length = 77.0
    elif "sw-geo_full" in folder_path:
        speed = 70.0
        length = 121.0
    elif "sw-schlee_2" in folder_path:
        speed = 65.0
        length = 60.0
    elif "sw-schlee_3" in folder_path:
        speed = 65.0
        length = 93.0
    elif "sw-schlee_full" in folder_path:
        speed = 65.0
        length = 130.0
    else:
        raise ValueError

    try:
        print(f"Running C-code in: {folder_path}")
        result = subprocess.run([C_EXECUTABLE, folder_path, str(speed), str(length), OUTPUT_PATH], check=True, text=True)
        print(f"Output:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error running C-code in {folder_path}:\n{e.stderr}")

def walk_and_run(directory):
    """Recursively walk through folders and run C-code."""
    for root, dirs, files in os.walk(directory):
        for file_name in files:
            if file_name[-5] != 'a':
                full_path = os.path.join(root, file_name)
                print("Found file:", full_path)
                #full_path = os.path.join(root, file)
                run_c_code(full_path, file_name)

if __name__ == "__main__":
    walk_and_run(ROOT_DIR)
