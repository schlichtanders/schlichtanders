#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
import re

__author__ = 'Stephan Sahm <Stephan.Sahm@gmx.de>'

def replace_all(orig, replace_dict):
    for k, v in replace_dict.items():
        orig = orig.replace(k, v)  # copies string
    return orig

def append_after(orig, string, split_regex=None):
    """ if split_regex is given, string is appended after each split + split_regex.match (multiline mode)"""
    if split_regex is None:
        return orig + string
    else:
        splitted = re.split(r"(%s)" % split_regex, orig, flags=re.MULTILINE)
        new = ""
        while len(splitted) > 1:
            new += splitted.pop(0) + splitted.pop(0) + string
        new += splitted.pop()  # even works if match matches end
        return new