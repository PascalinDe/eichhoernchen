#    This file is part of Eichhoernchen 2.2.
#    Copyright (C) 2018-2021  Carine Dengler
#
#    Eichhoernchen is free software: you can redistribute it and/or modify
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
:synopsis: Configuration file handling test cases.
"""


# standard library imports
import os
import tempfile
import unittest
import configparser

from pathlib import Path

# third party imports
# library specific imports
import src.config


class TestConfig(unittest.TestCase):
    """Configuration file handling test cases."""

    def test_create_config(self):
        """Test creating configuration file.

        Trying: creating configuration file
        Expecting: configuration file has been created
        """
        config = configparser.ConfigParser()
        path = tempfile.NamedTemporaryFile(delete=False)
        src.config._create_config(path.name)
        with open(path.name) as fp:
            config.readfp(fp)
        self.assertIn("database", config.sections())
        self.assertEqual(config["database"]["dbname"], "eichhoernchen.db")
        self.assertEqual(
            config["database"]["path"],
            str(Path(os.environ["HOME"]) / ".local" / "share"),
        )
        path.close()

    def test_validate_config(self):
        """Test validating configuration file.

        Trying: validating configuration file
        Expecting: configuration file has been validated
        """
        config = configparser.ConfigParser()
        config["database"] = {
            "dbname": "eichhoernchen.db",
            "path": Path(os.environ["HOME"]) / ".local" / "share",
        }
        config["aliases"] = {"list": ["ls"]}
        self.assertIsNone(src.config._validate_config(config))

    def test_validate_config_required_section_missing(self):
        """Test validating configuration file.

        Trying: required section is missing
        Expecting: BuggyConfig has been raised
        """
        with self.assertRaises(src.config.BuggyConfig):
            src.config._validate_config(configparser.ConfigParser())

    def test_validate_config_required_key_missing(self):
        """Test validating configuration file.

        Trying: required key is missing
        Expecting: BuggyConfig has been raised
        """
        config = configparser.ConfigParser()
        config["database"] = {
            "dbname": "eichhoernchen.db",
        }
        with self.assertRaises(src.config.BuggyConfig):
            src.config._validate_config(config)

    def test_validate_config_unknown_command(self):
        """Test validating configuration file.

        Trying: unknown command in 'aliases' section
        Expecting: BuggyConfig has been raised
        """
        config = configparser.ConfigParser()
        config["database"] = {
            "dbname": "eichhoernchen.db",
            "path": Path(os.environ["HOME"]) / ".local" / "share",
        }
        config["aliases"] = {"foo": ["bar"]}
        with self.assertRaises(src.config.BuggyConfig):
            src.config._validate_config(config)
