""" plotting helpers """
from __future__ import division
from numpy import ma
import matplotlib as mpl
from matplotlib.colors import Normalize
import matplotlib.pyplot as plt
from contextlib import contextmanager
import numpy as np
from collections import Counter

__author__ = 'Stephan Sahm <Stephan.Sahm@gmx.de>'


# interactive plotting
# ====================

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


# colormaps
# =========

class Centre(Normalize):
    """ a Normalizer which centers a colorbar, etc., around a midpoint """
    def __init__(self, midpoint=0, vmin=None, vmax=None, clip=False):
        Normalize.__init__(self, vmin, vmax, clip)
        self.midpoint = midpoint

    def __call__(self, value, clip=None):
        if clip is None:
            clip = self.clip

        result, is_scalar = self.process_value(value)

        self.autoscale_None(result)
        vmin, vmax, midpoint = self.vmin, self.vmax, self.midpoint

#         if not (vmin < midpoint < vmax):
#             raise ValueError("midpoint must be between maxvalue and minvalue.")
        if midpoint < vmin:
            vmin = midpoint
        elif vmax < midpoint:
            vmax = midpoint
        elif vmin == vmax:
            result.fill(0) # Or should it be all masked? Or 0.5?
        elif vmin > vmax:
            raise ValueError("maxvalue must be bigger than minvalue")
        else:
            vmin = float(vmin)
            vmax = float(vmax)
            if clip:
                mask = ma.getmask(result)
                result = ma.array(np.clip(result.filled(vmax), vmin, vmax),
                                  mask=mask)

            # ma division is very slow; we can take a shortcut
            resdat = result.data

            #First scale to -1 to 1 range, than to from 0 to 1.
            resdat -= midpoint
            resdat[resdat>0] /= abs(vmax - midpoint)
            resdat[resdat<0] /= abs(vmin - midpoint)

            resdat /= 2.
            resdat += 0.5
            result = ma.array(resdat, mask=result.mask, copy=False)

        if is_scalar:
            result = result[0]
        return result

    def inverse(self, value):
        if not self.scaled():
            raise ValueError("Not invertible until scaled")
        vmin, vmax, midpoint = self.vmin, self.vmax, self.midpoint

        if mpl.cbook.iterable(value):
            val = ma.asarray(value)
            val = 2 * (val-0.5)
            val[val>0]  *= abs(vmax - midpoint)
            val[val<0] *= abs(vmin - midpoint)
            val += midpoint
            return val
        else:
            val = 2 * (val - 0.5)
            if val < 0:
                return  val*abs(vmin-midpoint) + midpoint
            else:
                return  val*abs(vmax-midpoint) + midpoint



# general helpers
# ===============

def gca():
    """ this version of gca won't create a new axis if none exists, however return None instead"""
    fig = plt.gcf()
    ckey, cax = fig._axstack.current_key_axes()
    if cax is None:
        return None
    return plt.gca()


@contextmanager
def useax(ax):
    """ sets current axes within scope and restores old axes on exits (can be nested) """
    if ax is not None:
        old_ax = gca()
        plt.sca(ax)
        yield
        if old_ax is not None:
            plt.sca(old_ax)
    else:
        yield


def to_colors(cluster, ignore_cnt=5):
    # group all small cluster together:
    cluster_count = Counter(cluster)
    ignore = set(k for k, v in cluster_count.items() if v <= ignore_cnt)

    unique_cluster = np.unique(cluster)
    unique_colors = {
        k: (0.0, 0.0, 0.0, 0.75) if k in ignore else plt.cm.Set1(l)  # (0.5, 0.5, 0.5, 0.75)
        for k, l in zip(unique_cluster, np.linspace(0, 1, num=len(unique_cluster), endpoint=False))
        }
    return np.array([unique_colors[k] for k in cluster])