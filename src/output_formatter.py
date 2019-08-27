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
:synopsis: Output formatter.
"""


# standard library imports
# third party imports
# library specific imports
from src.colour import GrmlVCSLikeColourScheme, MonochromeColourScheme
from src.template import Template


class OutputFormatter():
    """Output formatter.

    :ivar MonochromeColourScheme monochrome_scheme: monochrome colour scheme
    :ivar MonochromeColourScheme polychrome_scheme: polychrome colour scheme
    """

    def __init__(self):
        """Initialize output formatter."""
        self.monochrome_template = Template(MonochromeColourScheme())
        self.polychrome_template = Template(GrmlVCSLikeColourScheme())

    def pprint_name(self, name, colour=False):
        """Pretty-print name.

        :param str name: name
        :param bool colour: toggle coloured display on/off

        :returns: pretty-printed name
        :rtype: str
        """
        if colour:
            return self.polychrome_template.name.format(name=name)
        else:
            return self.monochrome_template.name.format(name=name)

    def pprint_tags(self, tags, colour=False):
        """Pretty-print tags.

        :param list tags: tags
        :param bool colour: toggle coloured display on/off

        :returns: pretty-printed tags
        :rtype: str
        """
        if colour:
            return "".join(
                self.polychrome_template.tag.format(tag=tag) for tag in tags
            )
        else:
            return "".join(
                self.monochrome_template.tag.format(tag=tag) for tag in tags
            )

    def pprint_full_name(self, name, tags, colour=False):
        """Pretty-print full name.

        :param str name: name
        :param list tags: tags
        :param bool colour: toggle coloured display on/off

        :returns: pretty-printed full name
        :rtype: str
        """
        name = self.pprint_name(name, colour=colour)
        tags = self.pprint_tags(tags, colour=colour)
        return self.monochrome_template.full_name.format(name=name, tags=tags)

    def pprint_time_span(self, time_span, date=False, colour=False):
        """Pretty-print time span.

        :param tuple time_span: time span
        :param bool date: toggle displaying date on/off
        :param bool colour: toggle coloured display on/off

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
        if colour:
            return self.polychrome_template.time_span.format(
                start=start, end=end
            )
        else:
            return self.monochrome_template.time_span.format(
                start=start, end=end
            )

    def pprint_total(self, total, colour=False):
        """Pretty-print representation of total runtime.

        :param int total: runtime (in seconds)

        :returns: pretty-printed representation of total runtime
        :rtype: str
        """
        minutes, seconds = divmod(total, 60)
        hours, minutes = divmod(minutes, 60)
        if colour:
            return self.polychrome_template.total.format(
                hours=hours, minutes=minutes
            )
        else:
            return self.monochrome_template.total.format(
                hours=hours, minutes=minutes
            )

    def pprint_task(self, task, date=False, colour=False):
        """Pretty-print representation of task.

        :param Task task: task
        :param bool date: toggle displaying date on/off
        :param bool colour: toggle coloured display on/off

        :returns: pretty-printed representation of task
        :rtype: str
        """
        full_name = self.pprint_full_name(
            task.name, task.tags, colour=colour
        )
        time_span = self.pprint_time_span(
            task.time_span, date=date, colour=colour
        )
        total = self.pprint_total(task.total, colour=colour)
        return self.monochrome_template.task.format(
            time_span=time_span, total=total, full_name=full_name
        )

    def pprint_sum(self, full_name, total, colour=False):
        """Pretty-print sum of total runtime.

        :param tuple full_name: full name
        :param int total: runtime (in seconds)
        :param bool colour: toggle coloured display on/off

        :returns: pretty-printed representation of total runtime
        :rtype: str
        """
        full_name = self.pprint_full_name(*full_name, colour=colour)
        total = self.pprint_total(total, colour=colour)
        return self.monochrome_template.sum.format(
            full_name=full_name, total=total
        )

    def pprint_prompt(self, task):
        """Pretty-print prompt.

        :param Task task: task

        :returns: prompt
        :rtype: str
        """
        if task.name:
            full_name = self.pprint_full_name(
                task.name, task.tags, colour=True
            )
            start, _ = task.time_span
            start = start.strftime("%H:%M")
            running = self.polychrome_template.running.format(
                full_name=full_name, start=start
            )
        else:
            running = ""
        return self.monochrome_template.prompt.format(running=running)
