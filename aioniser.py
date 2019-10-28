#!/usr/bin/env python

import argparse
import json
import os
from pathlib import Path
from tempfile import gettempdir


DEFAULT_CONFIG_FILE_PATH = Path('~/.config/aioniser.json').expanduser()
DEFAULT_STEP_STATE_FILE_PATH = Path(gettempdir()) / 'aioniser_steps.json'


def main():
    config_file_path = DEFAULT_CONFIG_FILE_PATH
    step_state_file_path = DEFAULT_STEP_STATE_FILE_PATH
    args = parse_args()
    actions, cycles = read_aioniser_config(config_file_path)
    cycle = cycles[args.cycle_name]
    step = cycle['steps'][get_next_step_no(
        step_state_file_path, args.cycle_name, len(cycle['steps'])
    )]
    for activity in step:
        action_name = activity['action']
        kwargs = activity['kwargs']
        action = actions[action_name].format(**kwargs)
        print(action)
        os.system(action)


def get_next_step_no(step_state_file_path, cycle_name, cycle_length):
    step_states = read_step_state_file(step_state_file_path)
    current_step_for_cycle = step_states.get(cycle_name, 0)
    next_step_for_cycle = (current_step_for_cycle + 1) % cycle_length
    step_states[cycle_name] = next_step_for_cycle
    write_step_state_file(step_state_file_path, step_states)
    return current_step_for_cycle


def read_step_state_file(step_state_file_path):
    try:
        with open(step_state_file_path) as step_state_input:
            step_states = json.load(step_state_input)
    except FileNotFoundError:
        step_states = {}
    return step_states


def write_step_state_file(step_state_file_path, step_states):
    with open(step_state_file_path, 'w') as step_state_input:
        json.dump(
            dict(sorted(step_states.items())), step_state_input, indent=4
        )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'cycle_name',
        metavar='CYCLE',
        help='Name of cycle in which to trigger a step'
    )
    return parser.parse_args()


def read_aioniser_config(config_path):
    with open(config_path) as config_input:
        config = json.load(config_input)
    return config['actions'], config['cycles']


if __name__ == '__main__':
    main()