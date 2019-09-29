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
import datetime
import unittest

# third party imports

# library specific imports
from src import argument_parser, FullName


class TestArgumentParser(unittest.TestCase):
    """Argument parser test cases."""

    def test_find_full_name(self):
        """Test finding full name.

        Trying: finding full name
        Expecting: full name and remaining command-line arguments
        """
        name = "foo"
        tags = {"bar", "baz"}
        remaining = "all"
        args = f"{name}{''.join(f'[{tag}]' for tag in tags)}{remaining}"
        full_name, args = argument_parser.find_full_name(args)
        self.assertEqual(full_name, FullName(name, tags))
        self.assertEqual(args, remaining)

    def test_find_time_span_date(self):
        """Test finding time span.

        Trying: finding date
        Expecting: time span and remaining command-line arguments
        """
        today = datetime.date.today()
        tomorrow = (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        today = today.strftime("%Y-%m-%d")
        expected = ((today, tomorrow), "")
        actual = argument_parser.find_time_span(
            f"@{today} @{tomorrow}", time=False
        )
        self.assertEqual(actual, expected)
        expected = (("today", ""), "")
        actual = argument_parser.find_time_span("@today", time=False)
        self.assertEqual(actual, expected)

    def test_find_time_span_time(self):
        """Test finding time span.

        Trying: finding time
        Expecting: time span and remaining command-line arguments
        """
        now = datetime.datetime.now()
        later = (now + datetime.timedelta(hours=1)).strftime("%H:%M")
        now = now.strftime("%H:%M")
        expected = ((now, later), "")
        actual = argument_parser.find_time_span(
            f"@{now} @{later}", date=False
        )
        self.assertEqual(actual, expected)
        expected = (("", ""), "@today")
        actual = argument_parser.find_time_span("@today", date=False)

    def test_find_time_span_datetime(self):
        """Test finding time span.

        Trying: finding date and time
        Expecting: time span and remaining command-line arguments
        """
        now = datetime.datetime.now()
        later = (now + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
        now = now.strftime("%Y-%m-%d %H:%M")
        expected = ((now, later), "")
        actual = argument_parser.find_time_span(
            f"@{now} @{later}"
        )
        self.assertEqual(actual, expected)
        expected = (("", ""), "@today")
        actual = argument_parser.find_time_span("@today")

    def test_find_summand(self):
        """Test finding summand.

        Trying: finding summand
        Expecting: summand and remaining command-line arguments
        """
        full_name = "full name"
        remaining = "all"
        args = f"{full_name}{remaining}"
        summand, args = argument_parser.find_summand(args)
        self.assertEqual(summand, full_name)
        self.assertEqual(args, remaining)
