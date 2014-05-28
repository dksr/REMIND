#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Color Table
~~~~~~~~~~~

Display a table of available console text formatting options (colors etc.)
using the escape character and `ANSI escape codes`_.

.. _ANSI escape codes: http://en.wikipedia.org/wiki/ANSI_escape_code

:Copyright: 2002-2008 Jochen Kupperschmidt
:Date: 18-Jun-2008
:License: MIT
"""

COLORS = ('black', 'red', 'green', 'yellow',
          'blue', 'magenta', 'cyan', 'white')
STYLES = (('foregr.', 30), ('backgr.', 40),
          ('bold', 1), ('faint', 2), ('italic',3 ),
          ('underl.', 4), ('blink', 5), ('reverse', 7))
COLUMN_SPACE = ' | '
ESC = chr(27) + '[%sm'
CELL_FORMAT = ESC + '%-7s' + (ESC % 0)  # 0 resets

def gen_column(value):
    """Generate a column with all color names, but the same style."""
    for index, color in enumerate(COLORS):
        if value >= 30:
            style = '%d' % (index + value)
        else:
            style = '%d;%d' % (30 + index, value)
        yield CELL_FORMAT % (style, color)

def build_table():
    """Generate table head and body rows."""
    # titles
    yield (('%-7s' % style[0]) for style in STYLES)

    # separators
    yield ['-' * 7] * len(STYLES)

    # rows
    for row in zip(*(gen_column(style[1]) for style in STYLES)):
        yield row

if __name__ == '__main__':
    # print table
    print
    print '\n'.join(map(COLUMN_SPACE.join, build_table()))
    print
