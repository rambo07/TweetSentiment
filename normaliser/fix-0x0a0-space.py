#!/usr/bin/env python

import sys

data = sys.stdin.read()

# v2 is in UTF-8

#data = data.replace('\xa0', ' ')

data = data.replace('\xc2\xa0', ' ')

sys.stdout.write(data)
