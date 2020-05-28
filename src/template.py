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
:synopsis: Templates.
"""


# standard library imports
# third party imports
# library specific imports


class Template():
    """Template."""

    @property
    def base_template(self):
        return "{template}"

    @property
    def name(self):
        return self.base_template.format(template="{name}")

    @property
    def tag(self):
        return self.base_template.format(template="[{tag}]")

    @property
    def time_span(self):
        return self.base_template.format(template="{start}-{end}")

    @property
    def total(self):
        return self.base_template.format(template="{hours}h{minutes}m")

    @property
    def prompt(self):
        return self.base_template.format(template="~>")
