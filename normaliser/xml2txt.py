#!/usr/bin/env python

import sys

example_input = """
        iPhoto is probably the best program I have ever worked with: easy and convenient.
        iPhotos is an excellent program for storing and organizing photos.
"""

while True:
    line = sys.stdin.readline()
    if not line:
        break
    if '&' in line:
        raise NotImplementedError
    print line

