#    Eichhörnchen 1.2
#    Copyright (C) 2018-2019  Carine Dengler
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
:synopsis: Eichhörnchen 1.1.
"""


# standard library imports
import argparse

# third party imports

# library specific imports
import src.shell


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        prog="Eichhörnchen",
        description="Command-line time tracking."
    )
    parser.add_argument("-c", "--config", help="use this configuration file")
    parser.add_argument(
        "--version", action="version", version="%(prog)s 1.2"
    )
    args = parser.parse_args()
    try:
        shell = src.shell.TaskShell(path=args.config)
        shell.cmdloop()
    except Exception as exception:
        print(exception)


if __name__ == "__main__":
    main()
