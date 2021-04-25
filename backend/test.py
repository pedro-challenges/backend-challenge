"""Test all levels at once"""

import os
import json
import pytest
import level1.rent
import level2.rent
import level3.rent
import level4.rent
import level5.rent


def get_file(relative_path):
    """Get file path from parameter and current path."""
    return os.path.join(os.path.dirname(__file__), relative_path)


def get_hook_output(level, module):
    """Return load_hook output for desired level."""
    with open(get_file("level" + level + "/data/input.json")) as fil:
        return json.load(fil, object_hook=module.load_hook)


def get_expected_output(level):
    """Return expect output for desired level."""

    with open(get_file("level" + level + "/data/expected_output.json")) as fil:
        return json.load(fil)


@pytest.mark.parametrize("test_input,expected", [
    (get_hook_output("1", level1.rent), get_expected_output("1")),
    (get_hook_output("2", level2.rent), get_expected_output("2")),
    (get_hook_output("3", level3.rent), get_expected_output("3")),
    (get_hook_output("4", level4.rent), get_expected_output("4")),
    (get_hook_output("5", level5.rent), get_expected_output("5"))
])
def test_hook(test_input, expected):
    """Assert all levels parametrized."""
    assert test_input == expected
