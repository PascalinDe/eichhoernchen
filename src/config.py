#    This file is part of Eichhörnchen 2.2.
#    Copyright (C) 2018-2021  Carine Dengler
#
#    Eichhörnchen is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
:synopsis: Configuration file utils.
"""


# standard library imports
import os
import configparser

from pathlib import Path

# third party imports
# library specific imports


REQUIRED_SECTIONS = {"database": {"dbname", "path"}}
KNOWN_SUBCOMMANDS = {
    "start",
    "stop",
    "add",
    "remove",
    "edit",
    "list",
    "clean_up",
    "sum",
    "export",
    "show_stats",
    "help",
    "aliases",
    "next",
    "previous",
}


class BuggyConfig(Exception):
    """Raised when configuration file contains errors."""

    pass


def _create_config(path):
    """Create configuration file.

    :param str path: path to configuration file
    """
    config = configparser.ConfigParser()
    config["database"] = {
        "dbname": "eichhoernchen.db",
        "path": str(Path(os.environ["HOME"]) / ".local" / "share"),
    }
    with open(path, "w") as fp:
        config.write(fp)


def _validate_config(config):
    """Validate configuration file.

    :param ConfigParser config: configuration

    :raises: BuggyConfig
    """
    for section, required in REQUIRED_SECTIONS.items():
        try:
            missing = ",".join(
                f"'{key}'" for key in required.difference(set(config[section].keys()))
            )
        except KeyError:
            raise BuggyConfig(f"required section '{section}' is missing")
        if missing:
            raise BuggyConfig(f"required key(s) {missing} are missing")
    try:
        unknown = ",".join(
            f"'{command}'"
            for command in set(config["aliases"].keys()).difference(KNOWN_SUBCOMMANDS)
        )
        if unknown:
            raise BuggyConfig(f"unknown command(s) {unknown}")
    except KeyError:
        pass


def load_config(path=""):
    """Load configuration file.

    :param str path: path to configuration file to load

    :raises: SystemExit

    :returns: configuration
    :rtype: dict
    """
    if not path:
        path = Path(os.environ["HOME"]) / ".config" / "eichhoernchen.ini"
        if not path.is_file():
            _create_config(str(path))
    config = configparser.ConfigParser()
    config.read(path)
    try:
        _validate_config(config)
    except BuggyConfig as exception:
        raise SystemExit(f"configuration file '{path}' contains errors: {exception}")
    return config
