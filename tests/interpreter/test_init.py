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
:synopsis: Command-line interpreter utils test cases.
"""


# standard library imports
import argparse
import datetime
import unittest

# third party imports
# library specific imports
import src.interpreter

from src import FullName


class TestInterpreterUtils(unittest.TestCase):
    """Command-line interpreter utils test cases."""

    def test_match_name(self):
        """Test matching name.

        Trying: match name
        Expecting: name if string contains name else ArgumentTypeError
        """
        for string, expected in (("foo", "foo"), ("foo$bar", "foo")):
            self.assertEqual(src.interpreter.match_name(string), expected)
        with self.assertRaises(argparse.ArgumentTypeError):
            src.interpreter.match_name("$foo")

    def test_match_tags(self):
        """Test matching tags.

        Trying: match tags
        Expecting: tags if string contains tags else ArgumentTypeError
        """
        expected = ("foo", "bar")
        tags = "".join(f"[{tag}]" for tag in expected)
        for string in (tags, "foo" + tags):
            self.assertCountEqual(src.interpreter.match_tags(string), expected)
        with self.assertRaises(argparse.ArgumentTypeError):
            src.interpreter.match_tags("")

    def test_match_full_name(self):
        """Test matching full name.

        Trying: match full name
        Expecting: full name if string contains full name or is empty string
        else ArgumentTypeError
        """
        for expected in (
            FullName("foo", frozenset(("bar", "baz"))),
            FullName("foo", frozenset()),
            FullName("", frozenset()),
        ):
            self.assertEqual(
                src.interpreter.match_full_name(
                    expected.name + "".join(f"[{tag}]" for tag in expected.tags)
                ),
                expected,
            )
        with self.assertRaises(argparse.ArgumentTypeError):
            src.interpreter.match_full_name("[foo]")

    def test_match_summand(self):
        """Test matching summand.

        Trying: match summand
        Expecting: summand if string contains summand or is empty string
        else ArgumentTypeError
        """
        for expected in (
            FullName("foo", frozenset(("bar", "baz"))),
            FullName("foo", frozenset()),
            FullName("", frozenset(("bar", "baz"))),
            FullName("", frozenset()),
        ):
            self.assertEqual(
                src.interpreter.match_summand(
                    expected.name + "".join(f"[{tag}]" for tag in expected.tags)
                ),
                expected,
            )
        with self.assertRaises(argparse.ArgumentTypeError):
            src.interpreter.match_summand("$foo")

    def test_match_from(self):
        """Test matching from.

        Trying: match from
        Expecting: from if string contains from else ArgumentTypeError
        """
        keywords = (
            "all",
            "year",
            "month",
            "week",
            "yesterday",
            "today",
        )
        for expected in (*keywords, datetime.datetime.now().strftime("%Y-%m-%d")):
            self.assertEqual(src.interpreter.match_from(f"@{expected}"), expected)
        with self.assertRaises(argparse.ArgumentTypeError):
            src.interpreter.match_from("foo")

    def test_match_to(self):
        """Test matching to.

        Trying: match to
        Expecting: to if string contains to else ArgumentTypeError
        """
        keywords = (
            "year",
            "month",
            "week",
            "yesterday",
            "today",
        )
        for expected in (*keywords, datetime.datetime.now().strftime("%Y-%m-%d")):
            self.assertEqual(src.interpreter.match_to(f"@{expected}"), expected)
        with self.assertRaises(argparse.ArgumentTypeError):
            src.interpreter.match_to("foo")

    def test_match_start(self):
        """Test matching start.

        Trying: match start
        Expecting: start if string contains start else ArgumentTypeError
        """
        now = datetime.datetime.now()
        for fmt_string in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%H:%M"):
            if fmt_string == "%H:%M":
                expected = now.strftime("%Y-%m-%d %H:%M")
            else:
                expected = now.strftime(fmt_string)
            self.assertEqual(
                src.interpreter.match_start(f"@{now.strftime(fmt_string)}"), expected
            )
        with self.assertRaises(argparse.ArgumentTypeError):
            src.interpreter.match_start("foo")

    def test_parse_datetime(self):
        """Test parsing datetime string.

        Trying: parse datetime string
        Expecting: datetime string if string is datetime string else ValueError
        """
        now = datetime.datetime.now()
        keywords = (
            "all",
            "year",
            "month",
            "week",
            "yesterday",
            "today",
        )
        for keyword in keywords:
            self.assertEqual(
                src.interpreter.parse_datetime(f"@{keyword}", keywords=keywords),
                keyword,
            )
        for fmt_string in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%H:%M"):
            if fmt_string == "%H:%M":
                expected = now.strftime("%Y-%m-%d %H:%M")
            else:
                expected = now.strftime(fmt_string)
            self.assertEqual(
                src.interpreter.parse_datetime(f"@{now.strftime(fmt_string)}"),
                expected,
            )
        for datetime_string in ("", "foo", "2021-13-01"):
            with self.assertRaises(argparse.ArgumentTypeError):
                src.interpreter.parse_datetime(datetime_string)
