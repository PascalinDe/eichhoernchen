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
:synopsis: Templates.
"""


# standard library imports
# third party imports
# library specific imports


class Template():
    """Template.

    :ivar MonochromeColourScheme scheme: colour scheme
    """

    def __init__(self, scheme):
        """Initialize template.

        :param MonochromeColourScheme scheme: colour scheme
        """
        self.scheme = scheme

    @property
    def base_template(self):
        return f"{self.scheme.default}{{template}}{self.scheme.default}"

    @property
    def name(self):
        return self.base_template.format(
            template=f"{self.scheme.name}{{name}}"
        )

    @property
    def tag(self):
        return self.base_template.format(
            template=f"{self.scheme.tag}[{{tag}}]"
        )

    @property
    def full_name(self):
        return self.base_template.format(template="{name}{tags}")

    @property
    def time_span(self):
        return self.base_template.format(
            template=f"{self.scheme.time_span}{{start}}-{{end}}"
        )

    @property
    def total(self):
        return self.base_template.format(
            template=f"{self.scheme.total}{{hours}}h{{minutes}}m"
        )

    @property
    def task(self):
        return self.base_template.format(
            template="{time_span} ({total}) {full_name}"
        )

    @property
    def sum(self):
        return self.base_template.format(template="{full_name} {total}")

    @property
    def running(self):
        return self.base_template.format(
            template=(
                f"{{full_name}}({self.scheme.time_span}"
                f"{{start}}-{self.scheme.default})"
            )
        )

    @property
    def prompt(self):
        return self.base_template.format(template="{running}~> ")
