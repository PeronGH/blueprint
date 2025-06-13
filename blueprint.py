#!/usr/bin/env python3

import subprocess
import argparse
import json
from enum import Enum
from typing import Any


# Global configuration

DRY_RUN = True


class ExitCode(Enum):
    SUCCESS = 0
    ERROR = 1
    CONFIG_ERROR = 2


# Helpers


def ensure_type(value: Any, expected_type: type):
    if not isinstance(value, expected_type):
        raise TypeError(
            f"Expected {expected_type.__name__}, got {type(value).__name__}"
        )


# .system


def handle_system_defaults(config: dict):
    ensure_type(config, dict)

    # Collect all entries in the format (namespace, key, value)
    entries: list[tuple[str, str, Any]] = []
    for namespace, settings in config.items():
        ensure_type(settings, dict)
        for key, value in settings.items():
            entries.append((namespace, key, value))

    # TODO: Restore original values if any error occurs
    # For now, just write the new values
    for namespace, key, value in entries:
        command = [
            "defaults",
            "write",
            namespace,
            key,
        ]
        if isinstance(value, bool):
            command.append("-bool")
            command.append("true" if value else "false")
        elif isinstance(value, str):
            command.append(value)
        elif isinstance(value, int):
            command.append(str(value))
        elif isinstance(value, float):
            command.append(str(value))
        else:
            raise TypeError(f"Unsupported value type: {type(value).__name__}")

        print(".system.defaults: executing", " ".join(command))
        if DRY_RUN:
            continue
        subprocess.run(command, check=True)


def handle_system(config: dict):
    ensure_type(config, dict)
    if defaults_config := config.get("defaults"):
        handle_system_defaults(defaults_config)


# .packages


def handle_packages_homebrew(config: dict):
    ensure_type(config, dict)

    taps = config.get("taps", [])
    ensure_type(taps, list)
    brews = config.get("brews", [])
    ensure_type(brews, list)
    casks = config.get("casks", [])
    ensure_type(casks, list)
    mas_apps = config.get("mas_apps", {})  # name -> id
    ensure_type(mas_apps, dict)

    lines = []
    lines += [f"tap {json.dumps(tap)}" for tap in taps]
    lines += [f"brew {json.dumps(brew)}" for brew in brews]
    lines += [f"cask {json.dumps(cask)}" for cask in casks]
    lines += [
        f"mas {json.dumps(name)}, id: {json.dumps(app_id)}"
        for name, app_id in mas_apps.items()
    ]
    brewfile = "\n".join(lines)

    print(f".packages.homebrew: applying Brewfile:\n---\n{brewfile}\n---")
    if DRY_RUN:
        return
    subprocess.run(
        ["brew", "bundle", "upgrade", "--file=-"],
        input=brewfile,
        text=True,
        check=True,
    )
    subprocess.run(
        ["brew", "bundle", "cleanup", "--force"],
    )


def handle_packages(config: dict):
    ensure_type(config, dict)
    if homebrew_config := config.get("homebrew"):
        handle_packages_homebrew(homebrew_config)


# .programs


def handle_programs_git(config: dict):
    pass


def handle_programs(config: dict):
    ensure_type(config, dict)
    if git_config := config.get("git"):
        handle_programs_git(git_config)


# Main
def main():
    parser = argparse.ArgumentParser(
        description="Define the blueprint of your OS in JSON ."
    )
    parser.add_argument("config", type=str, help="Path to the configuration file")
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = json.load(f)

    ensure_type(config, dict)

    if system_config := config.get("system"):
        handle_system(system_config)

    if packages_config := config.get("packages"):
        handle_packages(packages_config)

    if programs_config := config.get("programs"):
        handle_programs(programs_config)


if __name__ == "__main__":
    main()
