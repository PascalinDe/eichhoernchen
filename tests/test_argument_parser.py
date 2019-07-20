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
# third party imports
# library specific imports
import src.argument_parser
from src import FullName


class TestArgumentParser(unittest.TestCase):
    """Argument parser test cases."""

    def test_parse_args(self):
        """Test command-line arguments parsing.

        Trying: parsing command-line arguments (searching for key words off)
        Expecting: args is full name
        """
        args = "foo[bar]"
        key_word = src.argument_parser.KeyWord()
        argument_parser = src.argument_parser.ArgumentParser()
        expected = src.argument_parser.Args(
            full_name=FullName(name="foo", tags=["bar"])
        )
        self.assertEqual(argument_parser.parse_args(args, key_word), expected)

    def test_parse_args_key_word(self):
        """Test command-line arguments parsing.

        Trying: parsing command-line arguments (searching for key words on)
        Expecting: args contains non-default key word values
        """
        from_ = "all"
        to = "year"
        summand = "name"
        args = f"{from_} {to} {summand}"
        key_word = src.argument_parser.KeyWord(
            full_name=False, from_=True, to=True, summand=True
        )
        argument_parser = src.argument_parser.ArgumentParser()
        expected = src.argument_parser.Args(
            from_=from_, to=to, summand=summand
        )
        self.assertEqual(argument_parser.parse_args(args, key_word), expected)
