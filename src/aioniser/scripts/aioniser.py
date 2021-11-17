#!/usr/bin/env python

"""aioniser.py"""

import argparse
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import gettempdir
from typing import Dict, List


DEFAULT_CONFIG_FILE_PATH = Path('~/.config/aioniser.json').expanduser()
DEFAULT_STEP_STATE_FILE_PATH = Path(gettempdir()) / 'aioniser_steps.json'

DEFAULT_RESET_TIMEOUT_MS = 1000


def main():
    args = parse_args()
    do_aioniser(
        DEFAULT_CONFIG_FILE_PATH,
        DEFAULT_STEP_STATE_FILE_PATH,
        args.cycle_name,
    )


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

    def __getitem__(self, index):
        return self.step_activities[index]

    def __len__(self):
        return len(self.step_activies)

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
    reset: bool
    steps: List[Step]

    def __len__(self):
        return len(self.steps)

    def dump(self):
        cycle_dict = {
            'name': self.name,
            'steps': [step.dump() for step in self.steps],
        }
        if self.reset:
            cycle_dict['reset'] = self.reset
        return cycle_dict

    @staticmethod
    def load(cycle_name: str, cycle_body: Dict):
        return Cycle(
            cycle_name,
            cycle_body.get('reset', False),
            [Step.load(step_actions) for step_actions in cycle_body['steps']],
        )


def do_aioniser(config_file_path, step_state_file_path, cycle_name):
    actions, cycles = read_aioniser_config(config_file_path)
    cycle = cycles[cycle_name]
    step_no = get_step_no_to_run(step_state_file_path, cycle)
    step = cycle.steps[step_no]
    for activity in step:
        action_name = activity.action
        kwargs = activity.kwargs
        action = actions[action_name].format(**kwargs)
        print(action)
        os.system(action)


def get_step_no_to_run(step_state_file_path: Path, cycle: Cycle) -> int:
    """
    Inspect the step state file; compute next step; update state file.

    Logic for computing step to perform:

        If never triggered before:
            Do step 0
        Else if has reset flag and last triggered >= 0.5s ago
            Do step 0
        Else:
            Do step (last_step + 1) % step_count

    """
    step_states = read_step_state_file(step_state_file_path)
    cycle_state = step_states.get(cycle.name)
    if not cycle_state:
        # Never run before
        step_to_perform = 0
    elif cycle.reset and check_timeout(cycle_state['last_stepped']):
        step_to_perform = 0
    else:
        step_to_perform = (cycle_state['last_step'] + 1) % len(cycle)
    step_states[cycle.name] = {
        'last_step': step_to_perform,
        'last_stepped': dump_timestamp(now()),
    }
    write_step_state_file(step_state_file_path, step_states)
    return step_to_perform


def check_timeout(timestamp_str: str) -> bool:
    timestamp = load_timestamp(timestamp_str)
    elapsed = now() - timestamp
    return elapsed > timedelta(milliseconds=DEFAULT_RESET_TIMEOUT_MS)


# Config file I/O


def read_aioniser_config(config_path):
    with open(config_path) as config_input:
        config = json.load(config_input)
    cycles = {
        cycle_name: Cycle.load(cycle_name, cycle_body)
        for cycle_name, cycle_body in config['cycles'].items()
    }
    return config['actions'], cycles


# Step file I/O


def read_step_state_file(step_state_file_path):
    try:
        with open(step_state_file_path) as step_state_input:
            step_states = json.load(step_state_input)
    except FileNotFoundError:
        step_states = {}
    return step_states


def write_step_state_file(step_state_file_path, step_states):
    with open(step_state_file_path, 'w') as step_state_input:
        json.dump(dict(sorted(step_states.items())), step_state_input, indent=4)


# Timestamp I/O


def now() -> datetime:
    return datetime.now(tz=timezone.utc)


def dump_timestamp(timestamp: datetime) -> str:
    return timestamp.isoformat(timespec='milliseconds')


def load_timestamp(timestamp_str: str) -> datetime:
    return datetime.fromisoformat(timestamp_str)


# Argument parsing and housekeeping


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'cycle_name', metavar='CYCLE', help='Name of cycle in which to trigger a step'
    )
    return parser.parse_args()


if __name__ == '__main__':
    main()
