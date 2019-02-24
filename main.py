#    Eichhörnchen 1.0
#    Copyright (C) 2018  Carine Dengler
#
#    This program is free software: you can redistribute it and/or modify
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
:synopsis:
"""


# standard library imports
# third party imports
# library specific imports
import src.shell
import src.sqlite


def main():
    """Main function."""
    try:
        sqlite = src.sqlite.SQLite()
        sqlite.create_table()
        shell = src.shell.Shell()
        shell.cmdloop()
    except Exception as exception:
        msg = "failed to run Eichhörnchen 1.0:{}".format(exception)
        raise RuntimeError(msg)
    return


if __name__ == "__main__":
    main()