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
:synopsis: Argument parser.
"""


# standard library imports
import re
import datetime

# third party imports
# library specific imports
from src import FullName


class ArgumentParser():
    """Argument parser.

    :cvar Pattern NAME_PATTERN: regular expression matching name
    :cvar Pattern TAG_PATTERN: regular expression matching tag
    :cvar Pattern FULL_NAME_PATTERN: regular expression matching full name
    :cvar Pattern ISODATE_PATTERN: regular expression matching ISO 8601 date
    :cvar Pattern FROM_PATTERN: regular expression matching from ...
    :cvar Pattern TO_PATTERN: regular expression matching ... to
    :cvar Pattern SUMMAND_PATTERN: regular expression matching summand
    """
    NAME_PATTERN = re.compile(r"(?:\w|\s|[!#+-?])+")
    TAG_PATTERN = re.compile(r"\[((?:\w|\s|[!#+-?])+)\]")
    FULL_NAME_PATTERN = re.compile(
        fr"({NAME_PATTERN.pattern})(?:{TAG_PATTERN.pattern})*"
    )
    ISODATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
    ISOTIME_PATTERN = re.compile(r"\d{2}:\d{2}")
    ISO_PATTERN = re.compile(
        fr"({ISODATE_PATTERN.pattern})?\s*({ISOTIME_PATTERN.pattern})"
    )
    TIME_PERIOD = ("all", "year", "month", "week", "yesterday", "today")
    TIME_PERIOD_PATTERN = re.compile(fr"{'|'.join(TIME_PERIOD)}")
    FROM_PATTERN = re.compile(
        fr"@({ISODATE_PATTERN.pattern}|{TIME_PERIOD_PATTERN.pattern})"
    )
    TO_PATTERN = re.compile(
        fr"@({ISODATE_PATTERN.pattern}|{'|'.join(TIME_PERIOD[1:])})"
    )
    SUMMAND_PATTERN = re.compile(r"full name|name|tag")

    def cast_to_datetime(self, args):
        """Cast command-line arguments to datetime object.

        :param str args: command-line arguments

        :returns: datetime object
        :rtype: datetime
        """
        iso_match = self.ISO_PATTERN.match(args)
        if not iso_match:
            raise ValueError(f"{args} is not YYYY-MM-DD hh:mm format")
        if not iso_match.group(1):
            now = datetime.datetime.now().strftime("%Y-%m-%d")
            args = f"{now} {args}"
        return datetime.datetime.strptime(args, "%Y-%m-%d %H:%M")

    def find_full_name(self, args):
        """Find full name.

        :param str args: command-line arguments

        :returns: full name and remaining command-line arguments
        :rtype: tuple
        """
        full_name_match = self.FULL_NAME_PATTERN.match(args)
        if full_name_match:
            name = full_name_match.group(1).strip()
            tags = set(self.TAG_PATTERN.findall(args))
            args = self.FULL_NAME_PATTERN.sub("", args, count=1).strip()
            return FullName(name=name, tags=tags), args
        return FullName("", ()), args

    def find_from(self, args):
        """Find from ... .

        :param str args: command-line arguments

        :returns: from ... and remaining command-line arguments
        :rtype: tuple
        """
        from_match = self.FROM_PATTERN.match(args)
        if from_match:
            args = self.FROM_PATTERN.sub("", args, count=1).strip()
            return from_match.group(1).strip(), args
        return "", args

    def find_to(self, args):
        """Find ... to.

        :param str args: command-line arguments

        :returns: ... to and remaining command-line arguments
        :rtype: tuple
        """
        to_match = self.TO_PATTERN.match(args)
        if to_match:
            args = self.TO_PATTERN.sub("", args).strip()
            return to_match.group(1), args
        return "", args

    def find_summand(self, args):
        """Find summand.

        :param str args: command-line arguments

        :returns: summand and remaining command-line arguments
        :rtype: tuple
        """
        summand_match = self.SUMMAND_PATTERN.match(args)
        if summand_match:
            args = self.SUMMAND_PATTERN.sub("", args).strip()
            return summand_match.group(0), args
        return "", args
