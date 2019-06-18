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
:synopsis: Input parser and output formatter.
"""


# standard library imports
import re
import collections

# third party imports
# library specific imports


TAG_PATTERN = re.compile(r"\[(\w+)\]")
PERIOD = ("all", "year", "month", "week", "yesterday", "today")
PERIOD_PATTERN = re.compile(fr"{'|'.join(PERIOD)}")
TO_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
LISTING = ("name", "tag")
LISTING_PATTERN = re.compile(fr"{'|'.join(LISTING)}")


FullName = collections.namedtuple("FullName", ("name", "tags"))
FullName.__new__.__defaults__ = ("", [])
Args = collections.namedtuple("Args", ("full_name", "period", "to", "listing"))
Args.__new__.__defaults__ = (FullName(), "today", "now", "name")


class FGColours():
    """Foreground colours."""
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    DEFAULT = "\033[0m"


class BGColours():
    """Background colours."""
    RED = "\033[41m"
    GREEN = "\033[42m"
    YELLOW = "\033[43m"
    BLUE = "\033[44m"
    MAGENTA = "\033[45m"
    CYAN = "\033[46m"
    WHITE = "\033[47m"


def _parse_full_name(args):
    """Parse full name.

    :param str args: command-line arguments

    :returns: full name
    :rtype: FullName
    """
    name = TAG_PATTERN.sub("", args)
    tags = TAG_PATTERN.findall(args)
    return FullName(name=name, tags=tags)


def parse_args(args, key_word=False):
    """Parse command-line arguments.

    :param str args: command-line arguments
    :param bool key_word: toggle searching for key words on/off

    :returns: command-line arguments
    :rtype: Args
    """
    if not key_word:
        args = Args(full_name=_parse_full_name(args))
    else:
        period_match = PERIOD_PATTERN.search(args)
        to_match = TO_PATTERN.search(args)
        listing_match = LISTING_PATTERN.search(args)
        args = Args()
        if period_match:
            period = period_match.group(0)
            args = args._replace(period=period)
        if to_match:
            to = to_match.group(0)
            args = args._replace(to=to)
        if listing_match:
            listing = listing_match.group(0)
            args = args._replace(listing=listing)
    return args


def pprint_name(name, colour=False):
    """Pretty-print name.

    :param str name: name
    :param bool colour: toggle coloured display on/off

    :returns: name
    :rtype: str
    """
    if colour:
        colour0 = FGColours.DEFAULT
        colour1 = FGColours.GREEN
    else:
        colour0 = colour1 = FGColours.DEFAULT
    name = f"{colour1}{name}{colour0}"
    return name


def pprint_tags(tags, colour=False):
    """Pretty-print tags.

    :param list tags: tags
    :param bool colour: toggle coloured display on/off

    :returns: tags
    :rtype: str
    """
    if colour:
        colour0 = FGColours.DEFAULT
        colour1 = BGColours.GREEN
        colour2 = FGColours.WHITE
    else:
        colour0 = colour1 = FGColours.DEFAULT
    tags = "".join(
        f"{colour0}[{colour1}{colour2}{tag}{colour0}]" for tag in tags
    )
    return tags


def pprint_full_name(name, tags, colour=False):
    """Pretty-print full name.

    :param str name: name
    :param list tags: tags
    :param bool colour: toggle coloured display on/off
    """
    name = pprint_name(name, colour=colour)
    tags = pprint_tags(tags, colour=colour)
    return f"{name}{tags}"


def pprint_time_span(time_span, date=False, colour=False):
    """Pretty-print time span.

    :param tuple time_span: time span
    :param bool date: toggle displaying date on/off
    :param bool colour: toggle coloured display on/off

    :returns: time span
    :rtype: str
    """
    if colour:
        colour0 = FGColours.DEFAULT
        colour1 = FGColours.MAGENTA
    else:
        colour0 = colour1 = FGColours.DEFAULT
    start, end = time_span
    if date:
        if (end - start).days >= 1:
            start = start.strftime("%Y-%m-%d %H:%M")
        else:
            start = start.strftime("%H:%M")
        end = end.strftime("%H:%M %Y-%m-%d")
    else:
        start = start.strftime("%H:%M")
        end = end.strftime("%H:%M")
    time_span = f"{colour1}{start}{colour0}-{colour1}{end}{colour0}"
    return time_span


def pprint_total(total, colour=False):
    """Pretty-print representation of total runtime.

    :param int total: runtime (in seconds)

    :returns: representation of total runtime
    :rtype: str
    """
    if colour:
        colour0 = FGColours.DEFAULT
        colour1 = FGColours.YELLOW
    else:
        colour0 = colour1 = FGColours.DEFAULT
    minutes, seconds = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    return f"total: {colour1}{hours}h{minutes}m{colour0}"


def pprint_task(task, date=False, colour=False):
    """Pretty-print representation of task.

    :param Task task: task
    :param bool date: toggle displaying task on/off
    :param bool colour: toggle coloured display on/off

    :returns: representation of task
    :rtype: str
    """
    full_name = pprint_full_name(task.name, task.tags, colour=colour)
    time_span = pprint_time_span(task.time_span, date=date, colour=colour)
    total = pprint_total(task.total, colour=colour)
    return f"{time_span} ({total}) {full_name}"


def pprint_sum(full_name, total):
    """Pretty-print sum of total runtime.

    :param tuple full_name: full name
    :param int total: runtime (in seconds)
    """
    name, tags = full_name
    full_name = pprint_full_name(name, tags, colour=True)
    total = pprint_total(total, colour=True)
    return f"{full_name} {total}"


def pprint_prompt(task):
    """Pretty-print prompt.

    :param Task task: task

    :returns: prompt
    :rtype: str
    """
    if task.name:
        full_name = pprint_full_name(task.name, task.tags, colour=True)
        colour0 = FGColours.DEFAULT
        colour1 = FGColours.MAGENTA
        start, _ = task.time_span
        start = start.strftime("%H:%M")
        prompt = f"{full_name}({colour1}{start}{colour0}-) ~>"
    else:
        prompt = "~> "
    return prompt
