#!/usr/bin/python
# -*- coding: utf-8 -*-
""" DEPRECATED in favour of mymatplotlib.py ... (interactive) plotting. This should probably be merged with mymatplotlib"""
from __future__ import division
import numpy as np

__author__ = 'Stephan Sahm <Stephan.Sahm@gmx.de>'

# TODO DEPRECATED - REMOVE THIS PACKAGE in favour of mymatplotlib.py (everything is already copied)

def plt_sync(plt_object, margin_size=0.1):
    """ updates a plot dynamically given a certain axes object (e.g. a line) """
    plt_object.axes.relim()
    plt_object.axes.autoscale_view()
    plt_object.axes.margins(margin_size, margin_size)
    plt_object.figure.tight_layout()
    plt_object.figure.canvas.draw()


def add_val(hl, val, iteration_nr=None, update_fig=True):
    """ adds a value to a given line handle with x=#iteartion in a dynamic way

    default iteration nr is extracted from ``hl`` """
    if iteration_nr is None:
        iteration_nr = len(hl.get_xdata())
    add_point(hl, x=iteration_nr, y=val, update_fig=update_fig)


def add_point(hl, x, y, update_fig=True):
    """ adds a value to a given line handle in a dynamic way """
    hl.set_xdata(np.append(hl.get_xdata(), x))
    hl.set_ydata(np.append(hl.get_ydata(), y))
    if update_fig:
        plt_sync(hl)