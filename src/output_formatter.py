#    This file is part of Eichhörnchen 1.2.
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
# third party imports
# library specific imports
from src import FullName, Task
from src.template import Template


TEMPLATE = Template()


def pprint_name(name):
    """Pretty-print name.

    :param str name: name

    :returns: pretty-printed name
    :rtype: str
    """
    return TEMPLATE.name.format(name=name)


def pprint_tags(tags):
    """Pretty-print tags.

    :param list tags: tags

    :returns: pretty-printed tags
    :rtype: str
    """
    return "".join(TEMPLATE.tag.format(tag=tag) for tag in sorted(tags))


def pprint_full_name(full_name):
    """Pretty-print full name.

    :param FullName full_name: full name

    :returns: pretty-printed full name
    :rtype: str
    """
    return TEMPLATE.full_name.format(
        name=pprint_name(full_name.name), tags=pprint_tags(full_name.tags)
    )


def pprint_time_span(time_span, date=False):
    """Pretty-print time span.

    :param tuple time_span: time span
    :param bool date: toggle displaying date on/off

    :returns: time span
    :rtype: str
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
    return TEMPLATE.time_span.format(start=start, end=end)


def pprint_total(total):
    """Pretty-print total runtime.

    :param int total: runtime (in seconds)

    :returns: pretty-printed representation of total runtime
    :rtype: str
    """
    minutes, _ = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    return TEMPLATE.total.format(hours=hours, minutes=minutes)


def pprint_task(task, date=False):
    """Pretty-print task.

    :param Task task: task
    :param bool date: toggle displaying date on/off

    :returns: pretty-printed task
    :rtype: str
    """
    return TEMPLATE.task.format(
        time_span=pprint_time_span(task.time_span, date=date),
        total=pprint_total(task.total),
        full_name=pprint_full_name(FullName(task.name, task.tags))
    )


def pprint_sum(full_name, total):
    """Pretty-print sum of total runtime.

    :param FullName full_name: full name
    :param int total: runtime (in seconds)

    :returns: pretty-printed total runtime
    :rtype: str
    """
    return TEMPLATE.sum.format(
        full_name=pprint_full_name(full_name), total=pprint_total(total)
    )


def pprint_prompt(task=Task("", set(), ())):
    """Pretty-print prompt.

    :param Task task: task

    :returns: pretty-printed prompt
    :rtype: str
    """
    if task.name:
        full_name = pprint_full_name(FullName(task.name, task.tags))
        start, _ = task.time_span
        start = start.strftime("%H:%M")
        return TEMPLATE.prompt.format(
            running=TEMPLATE.running.format(full_name=full_name, start=start)
        )
    return TEMPLATE.prompt.format(running="")
