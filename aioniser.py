#!/usr/bin/env python

"""aioniser.py

Desired new logic:

If never triggered before:
    If cycle has initial:
        This step is initial
    Else:
        This step is 0
Else if last triggered >= 0.5s ago:
    If cycle has initial:
        This step is initial
    Else:
        This step is last step + 1
Else:
    This step is last step + 1

"""

import argparse
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from pprint import pformat
from tempfile import gettempdir
from typing import Dict, List, Optional


DEFAULT_CONFIG_FILE_PATH = Path('~/.config/aioniser.json').expanduser()
DEFAULT_STEP_STATE_FILE_PATH = Path(gettempdir()) / 'aioniser_steps.json'


@dataclass
class Activity:
    action: str
    kwargs: Dict[str, str]

    def dump(self):
        return asdict(self)

    @staticmethod
    def load(action: str, kwargs: Dict[str, str]):
        return Activity(action, kwargs)


@dataclass
class Step:
    step_activities: List[Activity]

    def dump(self):
        return [activity.dump() for activity in self.step_activities]

    @staticmethod
    def load(step_activity_dicts: List):
        activities = [
            Activity.load(activity_dict['action'], activity_dict['kwargs'])
            for activity_dict in step_activity_dicts
        ]
        return Step(step_activities=activities)


@dataclass
class Cycle:
    name: str
    initial: Optional[Step]
    steps: List[Step]

    def dump(self):
        return {
            'name': self.name,
            'initial': self.initial.dump() if self.initial is not None else None,
            'steps': [step.dump() for step in self.steps],
        }

    @staticmethod
    def load(cycle_name: str, cycle_body: List):
        initial = cycle_body.get('initial')
        return Cycle(
            cycle_name,
            Step.load(initial) if initial is not None else None,
            [Step.load(step_actions) for step_actions in cycle_body['steps']],
        )


def main():
    config_file_path = DEFAULT_CONFIG_FILE_PATH
    step_state_file_path = DEFAULT_STEP_STATE_FILE_PATH
    args = parse_args()
    cycle_name = args.cycle_name
    actions, cycles, cycles_new = read_aioniser_config(config_file_path)
    cycle = cycles[cycle_name]
    step_no = get_step_no_to_run(
        step_state_file_path, cycle_name, len(cycle['steps'])
    )
    step = cycle['steps'][step_no]
    for activity in step:
        action_name = activity['action']
        kwargs = activity['kwargs']
        action = actions[action_name].format(**kwargs)
        print(action)
        os.system(action)


def get_step_no_to_run(
    step_state_file_path: Path,
    cycle_name: str,
    cycle_length: int,
) -> int:
    step_states = read_step_state_file(step_state_file_path)
    default_step_info = {
        'last_step': None,
        'last_stepped': None,
    }
    entry_for_cycle = step_states.get(cycle_name,default_step_info)
    last_step_for_cycle = entry_for_cycle['last_step']
    if last_step_for_cycle is None:
        current_step_for_cycle = 0
    else:
        current_step_for_cycle = (last_step_for_cycle + 1) % cycle_length
    step_states[cycle_name] = {
        'last_step': current_step_for_cycle,
        'last_stepped': now(),
    }
    write_step_state_file(step_state_file_path, step_states)
    return current_step_for_cycle


def now():
    return datetime.now(tz=timezone.utc).isoformat(timespec='milliseconds')


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
    cycles = {
        cycle_name: Cycle.load(cycle_name, cycle_body)
        for cycle_name, cycle_body in config['cycles'].items()
    }
    return config['actions'], config['cycles'], cycles


if __name__ == '__main__':
    main()