"""Get input from json file and write output.json proocessed output
by rent module."""

import sys
import os
import json
from rent import load_hook

def get_file_path(relative_path):
    """Get file path from argument and current path"""
    return os.path.join(os.path.dirname(__file__), relative_path)

def process_write_data(input_path, output_path):
    """Open input json, process data with load_hook and write output json"""
    with open(get_file_path(input_path)) as read_file:
        actions_output = json.load(read_file, object_hook=load_hook)

    with open(get_file_path(output_path), "w") as write_file:
        json.dump(actions_output, write_file, indent=2)
        write_file.write("\n")

if __name__ == "__main__":
    if len(sys.argv) == 3:
        process_write_data(sys.argv[1], sys.argv[2])
    else:
        process_write_data("data/input.json", "data/output.json")
