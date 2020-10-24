#    This file is part of Eichhörnchen 2.1.
#    Copyright (C) 2019  Carine Dengler
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
:synopsis: Configuration file handling.
"""


# standard library imports
import configparser
import os
import os.path

# third party imports
# library specific imports


class ConfigFound(Exception):
    """Raised when configuration file exists."""

    pass


class BadConfig(Exception):
    """Raised when configuration file contains errors."""

    pass


class ConfigNotFound(Exception):
    """Raised when configuration file does not exist."""

    pass


def _create_config():
    """Create configuration file."""
    path = os.path.join(os.environ["HOME"], ".config/eichhoernchen.ini")
    if os.path.exists(path):
        raise ConfigFound(f"configuration file {path} already exists")
    config = configparser.ConfigParser()
    config["database"] = {
        "dbname": "eichhoernchen.db",
        "path": os.path.join(os.environ["HOME"], ".local/share"),
    }
    with open(path, "w") as fp:
        config.write(fp)


def _validate_config(config):
    """Validate configuration file.

    :param ConfigParser config: configuration

    :raises: BadConfig when required section or key(s) are missing
    """
    check = {"database": {"dbname", "path"}}
    for section, required in check.items():
        try:
            missing = ",".join(
                f"'{key}'" for key in required.difference(set(config[section].keys()))
            )
        except KeyError:
            raise BadConfig(f"required section '{section}' is missing")
        if missing:
            raise BadConfig(f"required key(s) {missing} are missing")


def _read_config(path):
    """Read configuration file.

    :param str path: path to configuration file

    :returns: configuration
    :rtype: ConfigParser
    """
    if not os.path.exists(path):
        raise ConfigNotFound(f"configuration file {path} does not exist")
    else:
        config = configparser.ConfigParser()
        config.read(path)
    _validate_config(config)
    return config


def load_config(path=""):
    """Load configuration file.

    :param str path: path to configuration file

    :raises: SystemExit when configuration file contains errors

    :returns: configuration
    :rtype: dict
    """
    if not path:
        try:
            _create_config()
        except ConfigFound:
            pass
        path = os.path.join(os.environ["HOME"], ".config/eichhoernchen.ini")
    try:
        return _read_config(path)
    except BadConfig as exception:
        raise SystemExit(f"configuration file contains errors:\t{exception}")
