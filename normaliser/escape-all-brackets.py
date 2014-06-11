#!/usr/bin/env python
# -*- coding: utf-8 -*-

# (C) 2014 Dublin City University
# All rights reserved. This material may not be
# reproduced, displayed, modified or distributed without the express prior written
# permission of the copyright holder.

# Author: Joachim Wagner

import re
import sys

while True:
    line = sys.stdin.readline()
    if not line:
        break
    line = line.replace('(', '-LRB-')
    line = line.replace(')', '-RRB-')
    for other_lb in '{[<':
        line = line.replace(other_lb, '-LCB-')
    for other_rb in '}]>':
        line = line.replace(other_rb, '-RCB-')
    sys.stdout.write(line)
 

