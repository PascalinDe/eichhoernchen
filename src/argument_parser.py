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


def find_datetime(args, normalise=True):
    """Find date and/or time.

    :param str args: command-line arguments
    :param bool normalise: toggle returning normalised string on/off

    :returns: normalised string or datetime object
    :rtype: string or datetime
    """
    for format_string in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%H:%M"):
        try:
            datetime_obj = datetime.datetime.strptime(args, format_string)
            if format_string == "%H:%M":
                now = datetime.datetime.now()
                datetime_obj = datetime.datetime(
                    now.year, now.month, now.day,
                    datetime_obj.hour, datetime_obj.minute
                )
            break
        except ValueError:
            continue
    else:
        raise ValueError(
            f"time data '{args}' does not match any supported format"
        )
    if normalise:
        return datetime_obj.strftime("%Y-%m-%d %H:%M")
    else:
        return datetime_obj


def find_time_span(args, normalise=True):
    """Find time span.

    :param str args: command-line arguments
    :param bool normalise: toggle returning normalised string on/off

    :returns: time span and remaining command-line arguments
    :rtype: tuple
    """
    time_periods = ("year", "month", "week", "yesterday", "today")
    time_period_pattern = r"|".join(time_periods)
    iso_date_pattern = r"\d{4}-\d{2}-\d{2}"
    iso_time_pattern = r"\d{2}:\d{2}"
    iso_pattern = r"|".join(
        (
            fr"{iso_date_pattern}\s+{iso_time_pattern}",
            fr"{iso_date_pattern}",
            fr"{iso_time_pattern}"
        )
    )
    start_pattern = fr"all|{time_period_pattern}|{iso_pattern}"
    end_pattern = fr"{time_period_pattern}|{iso_pattern}"
    time_span_pattern = re.compile(
        fr"@({start_pattern})(?:\s+@({end_pattern}))?"
    )
    time_span_match = time_span_pattern.match(args)
    if time_span_match:
        start, end = time_span_match.groups()
        args = time_span_pattern.sub("", args, count=1).strip()
        if start not in ("all", ) + time_periods:
            start = find_datetime(start, normalise=normalise)
        if not end:
            end = ""
        elif end not in time_periods:
            end = find_datetime(end, normalise=normalise)
        return (start, end), args
    return ("", ""), args


def find_full_name(args):
    """Find full name.

    :param str args: command-line arguments

    :returns: full name and remaining command-line arguments
    :rtype: tuple
    """
    name_pattern = r"(?:\w|\s|[!#+-?])+"
    tag_pattern = fr"\[({name_pattern})\]"
    full_name_pattern = re.compile(fr"({name_pattern})(?:{tag_pattern})*")
    full_name_match = full_name_pattern.match(args)
    if full_name_match:
        name = full_name_match.group(1).strip()
        tags = set(re.findall(tag_pattern, args))
        args = full_name_pattern.sub("", args, count=1).strip()
        return FullName(name=name, tags=tags), args
    return FullName("", ()), args


def find_summand(args):
    """Find summand.

    :param str args: command-line arguments

    :returns: summand and remaining command-line arguments
    :rtype: tuple
    """
    summand_pattern = re.compile(r"full name|name|tag")
    summand_match = summand_pattern.match(args)
    if summand_match:
        args = summand_pattern.sub("", args).strip()
        return summand_match.group(0), args
    return "", args
