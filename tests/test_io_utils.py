#    This file is part of Eichhörnchen 1.0.
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
:synopsis: Input parser and output formatter test cases.
"""


# standard library imports
import unittest

# third party imports
# library specific imports
import src.io_utils


class TestIOUtils(unittest.TestCase):
    """Input parser and output formatter test cases."""

    def test_parse_args(self):
        """Test command-line arguments parsing.

        Trying: parsing command-line arguments (searching for key words off)
        Expecting: args is full name
        """
        args = "foo[bar]"
        expected = src.io_utils.Args(
            full_name=src.io_utils.FullName(name="foo", tags=["bar"])
        )
        self.assertEqual(src.io_utils.parse_args(args), expected)

    def test_parse_args_key_word(self):
        """Test command-line arguments parsing.

        Trying: parsing command-line arguments (searching for key words on)
        Expecting: args is list of key words
        """
        args = "all"
        expected = src.io_utils.Args(all="all")
        self.assertEqual(
            src.io_utils.parse_args(args, key_word=True), expected
        )
