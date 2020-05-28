#    This file is part of Eichhörnchen 2.0.
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
:synopsis: Output formatter.
"""


# standard library imports
import curses

# third party imports
# library specific imports
from src import FullName, Task
from src.template import Template


TEMPLATE = Template()


def pprint_name(name):
    """Pretty-print name.

    :param str name: name

    :returns: pretty-printed name
    :rtype: tuple
    """
    return ((TEMPLATE.name.format(name=name), curses.color_pair(1)),)


def pprint_tags(tags):
    """Pretty-print tags.

    :param list tags: tags

    :returns: pretty-printed tags
    :rtype: tuple
    """
    return (
        ("".join(TEMPLATE.tag.format(tag=tag) for tag in sorted(tags) if tag),
         curses.color_pair(2)),
    )


def pprint_full_name(full_name):
    """Pretty-print full name.

    :param FullName full_name: full name

    :returns: pretty-printed full name
    :rtype: tuple
    """
    return pprint_name(full_name.name) + pprint_tags(full_name.tags)


def pprint_time_span(time_span, date=False):
    """Pretty-print time span.

    :param tuple time_span: time span
    :param bool date: toggle displaying date on/off

    :returns: time span
    :rtype: tuple
    """
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
    return (
        (
            TEMPLATE.time_span.format(start=start, end=end),
            curses.color_pair(3)
        ),
    )


def pprint_total(total):
    """Pretty-print total runtime.

    :param int total: runtime (in seconds)

    :returns: pretty-printed representation of total runtime
    :rtype: tuple
    """
    minutes, _ = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    return (
        (
            TEMPLATE.total.format(hours=hours, minutes=minutes),
            curses.color_pair(4)
        ),
    )


def pprint_task(task, date=False):
    """Pretty-print task.

    :param Task task: task
    :param bool date: toggle displaying date on/off

    :returns: pretty-printed task
    :rtype: tuple
    """
    return (
        *pprint_time_span(task.time_span, date=date),
        ("(", curses.color_pair(0)),
        *pprint_total(task.total),
        (")", curses.color_pair(0)),
        *pprint_full_name(FullName(task.name, task.tags))
    )


def pprint_sum(full_name, total):
    """Pretty-print sum of total runtime.

    :param FullName full_name: full name
    :param int total: runtime (in seconds)

    :returns: pretty-printed total runtime
    :rtype: tuple
    """
    return (
        *pprint_full_name(full_name),
        (" ", curses.color_pair(0)),
        *pprint_total(total)
    )


def pprint_prompt(task=Task("", set(), ())):
    """Pretty-print prompt.

    :param Task task: task

    :returns: pretty-printed prompt
    :rtype: tuple
    """
    if task.name:
        full_name = pprint_full_name(FullName(task.name, task.tags))
        start, _ = task.time_span
        start = start.strftime("%H:%M")
        return (
            *full_name,
            ("(", curses.color_pair(0)),
            ("{start}-".format(start=start), curses.color_pair(3)),
            (")", curses.color_pair(0)),
            (TEMPLATE.prompt, curses.color_pair(0))
        )
    return ((TEMPLATE.prompt, curses.color_pair(0)),)
