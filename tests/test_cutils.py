#    This file is part of Eichhoernchen 2.2.
#    Copyright (C) 2021  Carine Dengler
#
#    Eichhoernchen is free software: you can redistribute it and/or modify
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
:synopsis: Curses utils test cases.
"""


# standard library imports
import unittest

# third party imports
# library specific imports
from src.cutils import Buffer


class TestBuffer(unittest.TestCase):
    """Buffer test cases.

    :ivar Buffer buffer: buffer
    """

    def setUp(self):
        """Set buffer test cases up."""
        self.buffer = Buffer("abcdefghijklmnopqrstuvwxyz")

    def test_append(self):
        """Test adding an item to the end of the list.

        Trying: adding an item to the end of the list
        Expecting: cursor position is only updated if it is at the end of the buffer
        """
        for i in (0, 8, len(self.buffer.data) - 1):
            self.buffer._pos = i
            cursor = self.buffer.cursor
            self.buffer.append("ä")
            if i == len(self.buffer.data) - 1:
                cursor = "ä"
            self.assertEqual(self.buffer.cursor, cursor)

    def test_extend(self):
        """Test extending the list.

        Trying: extending the list
        Extending: cursor position is only updated if it is at the end of the buffer
        """
        for i in (0, 8, len(self.buffer.data) - 1):
            self.buffer._pos = i
            cursor = self.buffer.cursor
            self.buffer.extend("äöü")
            if i == len(self.buffer.data) - 1:
                cursor = "ü"
            self.assertEqual(self.buffer.cursor, cursor)

    def test_insert(self):
        """Test inserting an item at a given position.

        Trying: inserting an item at a given position
        Expecting: cursor position is never updated
        """
        for i in (0, 8, len(self.buffer.data) - 1):
            self.buffer._pos = 16
            cursor = self.buffer.cursor
            self.buffer.insert(i, "ä")
            self.assertEqual(self.buffer.cursor, cursor)

    def test_remove(self):
        """Test removing first item x from the list.

        Trying: removing item
        Expecting: cursor position is only updated if it is at the item
        """
        self.buffer._pos = 8
        expected = self.buffer.data[self.buffer._pos - 1]
        for i in (0, 8, len(self.buffer.data) - 3):
            if i != self.buffer._pos:
                expected = self.buffer.cursor
            self.buffer.remove(self.buffer.data[i])
            self.assertEqual(self.buffer.cursor, expected)

    def test_pop(self):
        """Test removing and returning the item at the given position.

        Trying: removing and returning the item at the given position
        Expecting: cursor position is only updated if it is at the item
        """
        self.buffer._pos = 8
        expected = self.buffer.data[self.buffer._pos - 1]
        for i in (0, 8, len(self.buffer.data) - 3):
            if i != self.buffer._pos:
                expected = self.buffer.cursor
            self.buffer.pop(i)
            self.assertEqual(self.buffer.cursor, expected)

    def test_clear(self):
        """Test removing all items from the list.

        Trying: removing all items from the list
        Expecting: empty buffer
        """
        self.buffer.clear()
        with self.assertRaises(IndexError):
            self.buffer.cursor

    def test_reverse(self):
        """Test reversing the elements of the list.

        Trying: reversing the elements of the list
        Expecting: cursor position is not updated
        """
        for i in (0, 8, len(self.buffer.data) - 1):
            self.buffer._pos = i
            expected = self.buffer.cursor
            self.buffer.reverse()
            self.assertEqual(self.buffer.cursor, expected)

    def test_move(self):
        """Test moving cursor position n steps to the right.

        Trying: moving cursor position
        Expecting: cursor position is updated
        """
        for i in (0, len(self.buffer.data)):
            with self.assertRaises(IndexError):
                self.buffer._pos = i
                self.buffer.move(-1 if i == 0 else 1)
        i = 8
        for j in (-2, 2):
            self.buffer._pos = i
            expected = self.buffer.data[i + j]
            self.buffer.move(j)
            self.assertEqual(self.buffer.cursor, expected)

    def test_move_to_start(self):
        """Move cursor position to start.

        Trying: moving cursor position to start
        Expecting: cursor position is updated
        """
        self.buffer._pos = 8
        self.buffer.move_to_start()
        self.assertEqual(self.buffer.cursor, self.buffer.data[0])

    def test_move_to_end(self):
        """Move cursor position to end.

        Trying: moving cursor position to end
        Expecting: cursor position is updated
        """
        self.buffer._pos = 8
        self.buffer.move_to_end()
        self.assertEqual(self.buffer.pos, len(self.buffer.data))
