#    This file is part of Eichhörnchen 2.1.
#    Copyright (C) 2020  Carine Dengler
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
:synopsis: Parser.
"""


# standard library imports
import re
import datetime

# third party imports
# library specific imports


def parse_time(string, time_periods=tuple()):
    """Parse string containing time.

    :param str string: string
    :param tuple time_periods: time periods

    :raises ValueError: when date string does not match any format

    :returns: time
    :rtype: str
    """
    if time_periods:
        match = re.match(r"|".join(time_periods), string)
        if match:
            return match.group(0)
    for format_string in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%H:%M"):
        try:
            datetime.datetime.strptime(string, format_string)
        except ValueError:
            continue
        if format_string == "%H:%M":
            now = datetime.datetime.now()
            string = f"{now.year}-{now.month}-{now.day} {string}"
        return string
    else:
        raise ValueError(f"string '{string}' does not match any format")


def parse_from(string):
    """Parse string containing start of time span.

    :param str string: string

    :returns: start of time span
    :rtype: str
    """
    return parse_time(
        string, time_periods=("all", "year", "month", "week", "yesterday", "today")
    )


def parse_to(string):
    """Parse string containing end of time span.

    :param str string: string

    :returns: end of time span
    :rtype: str
    """
    return parse_time(
        string, time_periods=("year", "month", "week", "yesterday", "today")
    )


def parse_tags(string):
    """Parse string containing tags.

    :param str string: string

    :raises ValueError: when string does not contain any tags

    :returns: list of tags
    :rtype: set
    """
    matches = re.findall(r"\[((?:\w|\s|[!#+-?])+)\]", string)
    if matches:
        return set(tag.strip() for tag in matches)
    raise ValueError(f"string '{string}' does not contain any tags")


def parse_name(string):
    """Parse string containing name.

    :param str string: string

    :raises ValueError: when string is not name

    :returns: name
    :rtype: str
    """
    match = re.match(r"(?:\w|\s|[!#+-?])+", string)
    if match:
        return match.group(0).strip()
    raise ValueError(f"string '{string}' is not name")
