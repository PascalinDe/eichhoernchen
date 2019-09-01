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
:synopsis: Argument parser test cases.
"""


# standard library imports
import unittest
import datetime

# third party imports

# library specific imports
import src.argument_parser
from src import FullName


class TestArgumentParser(unittest.TestCase):
    """Argument parser test cases."""

    def setUp(self):
        """Set test cases up."""
        self.argument_parser = src.argument_parser.ArgumentParser()

    def test_find_full_name(self):
        """Test finding full name.

        Trying: finding full name
        Expecting: full name and remaining command-line arguments
        """
        name = "foo"
        tags = {"bar", "baz"}
        remaining = "all"
        args = f"{name}{''.join(f'[{tag}]' for tag in tags)}{remaining}"
        full_name, args = self.argument_parser.find_full_name(args)
        self.assertEqual(full_name, FullName(name, tags))
        self.assertEqual(args, remaining)

    def test_find_from(self):
        """Test finding from ... .

        Trying: finding from ...
        Expecting: from ... and remaining command-line arguments
        """
        now = datetime.datetime.now()
        yesterday = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        remaining = now.strftime("%Y-%m-%d")
        args = f"@{yesterday}{remaining}"
        from_, args = self.argument_parser.find_from(args)
        self.assertEqual(from_, yesterday)
        self.assertEqual(args, remaining)

    def test_find_to(self):
        """Test finding ... to.

        Trying: finding ... to
        Expecting: ... to and remaining command-line arguments
        """
        now = datetime.datetime.now()
        today = now.strftime("%Y-%m-%d")
        remaining = f"foo[bar][baz]"
        args = f"@{today}{remaining}"
        to, args = self.argument_parser.find_to(args)
        self.assertEqual(to, today)
        self.assertEqual(args, remaining)

    def test_find_summand(self):
        """Test finding summand.

        Trying: finding summand
        Expecting: summand and remaining command-line arguments
        """
        full_name = "full name"
        remaining = "all"
        args = f"{full_name}{remaining}"
        summand, args = self.argument_parser.find_summand(args)
        self.assertEqual(summand, full_name)
        self.assertEqual(args, remaining)
