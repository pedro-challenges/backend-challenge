"""Compare input.json and expected_output.json using pytest.
Run: pytest test.py (requires pytest module)"""

import os
import json
import rent
import main

def get_file(relative_path):
    """Get file path from parameter and current path."""
    return os.path.join(os.path.dirname(__file__), relative_path)

def test_hook():
    """Test rent.load_hook."""
    with open(get_file("data/input.json")) as read_file:
        rentals_output = json.load(read_file, object_hook=rent.load_hook)

    with open(get_file("data/expected_output.json")) as read_file:
        expected_output = json.load(read_file)

    assert rentals_output == expected_output

def test_files():
    """Compare input and output files."""
    main.process_write_data("data/input.json", "data/output.json")

    with open(get_file("data/output.json")) as read_file:
        output = json.load(read_file)

    with open(get_file("data/expected_output.json")) as read_file:
        expected_output = json.load(read_file)

    assert output == expected_output
