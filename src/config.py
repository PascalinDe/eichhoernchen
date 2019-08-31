#    This file is part of Eichhörnchen 1.1.
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
:synopsis:
"""


# standard library imports
import configparser
import os
import os.path

# third party imports
# library specific imports
import src.colour


COLOUR_SCHEMES = {
    "GrmlVCSLike": src.colour.GrmlVCSLikeColourScheme
}


class ConfigFound(Exception):
    """Raised when configuration file exists."""
    pass


class BadConfig(Exception):
    """Raised when configuration file contains errors."""
    pass


class ConfigNotFound(Exception):
    """Raised when configuration file does not exist."""


def create_config(force=False):
    """Create configuration file.

    :param bool force: toggle overwriting configuration file on/off
    """
    path = os.path.join(os.environ["HOME"], ".config/eichhoernchen.ini")
    if os.path.exists(path) and not force:
        raise ConfigFound(f"configuration file {path} already exists")
    else:
        config = configparser.ConfigParser()
        config["DEFAULT"] = {
            "database": "eichhoernchen.db",
            "path": os.path.join(os.environ["HOME"], ".local/share"),
            "colour_scheme": "GrmlVCSLike"
        }
        config["CUSTOM"] = {}
        with open(path, "w") as fp:
            config.write(fp)


def read_config(path):
    """Read configuration file.

    :param str path: path to configuration file

    :returns: configuration
    :rtype: dict
    """
    if not os.path.exists(path):
        raise ConfigNotFound(f"configuration file {path} does not exist")
    else:
        config = configparser.ConfigParser()
        config.read(path)
    config = dict(config["CUSTOM"])
    try:
        colour_scheme = COLOUR_SCHEMES[config["colour_scheme"]]
    except KeyError:
        raise BadConfig(f"unknown colour scheme {config['colour_scheme']}")
    config["colour_scheme"] = colour_scheme
    return config
