#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function, division

__author__ = 'Stephan Sahm <Stephan.Sahm@gmx.de>'

"""
This module captures high-level add-ons to the pyparsing interface (extended by Repeat-class).

Because we might work with several different implementations of the pyparsing interface, these
abstract helpers should not depend on a concrete realization and there have to be imported in a
special manner, by using `execfile`::

    _, pathname, _ = imp.find_module('_helpers_pyparsing_dep')
    execfile(pathname)

As this might through some errors, better also append the folder where the module lies to sys.path.
E.g. if it is in the current script-folder do the following::

    import os
    __path__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__path__)
"""

# more complex loading of parsing module as ordereddict variation reveals to be extremely slow
# (factor of 10 compared to standard package)
# thus standard is now to use classical package

# use_pyparsing_variant = os.environ.get('PYMSCONS_PYPARSING', "")
# if use_pyparsing_variant:
#     print "Helpers Pyparsing: Found request for using pyparsing", use_pyparsing_variant
#
# if not use_pyparsing_variant:
#     pass
#     # do nothing - enables use by execfile(...)
# elif use_pyparsing_variant in ["original", "ori", "pyparsing"]:
#     from pyparsing import *
#     from ._helpers_pyparsing_core import *
# elif use_pyparsing_variant in ["OD", "od", "ordereddict", "OrderedDict"]:
#     from pyparsingOD import *
# elif use_pyparsing_variant in ["regex", "re", "Re", "Regex"]:
#     from pyparsing_regex import *
# else:
#     raise RuntimeError("unkown pyparsing version specified in env PYMSCONS_PYPARSING")

#ParserElement.enablePackrat() #in this case it is slower...

def dictOf0(key, value):
    """ equals dictOf function, only more explicit notation

    :param key: expr to match key of key-value pair
    :param value: expr to match value of key-value pair (should follow key with possible intermediate whitespaces)
    :return: Dict-type of parser expression mapping every parsed key to the respectively (subsequently) parsed value
    """
    return Dict(ZeroOrMore(Group(key + value)))

def dictOf1(key, value):
    """ variant of dictOf function, using OneOrMore at its core

    :param key: expr to match key of key-value pair
    :param value: expr to match value of key-value pair (should follow key with possible intermediate whitespaces)
    :return: Dict-type of parser expression mapping every parsed key to the respectively (subsequently) parsed value
    """
    return Dict(OneOrMore(Group(key + value)))

def MatchAfter(indicator, expr):
    """ Capsulation of generic pattern. Only search for expr after searching for indicator.

    :param indicator: search for this first (but suppress)
    :param expr: search for this afterwards (and return)
    :return: ParseResult from expr
    """
    return Combine(Suppress(indicator + SkipTo(expr)) + expr)


# def setResultsNameInPlace(expr, name, listAllMatches=False):
#     """ adds resultsname in place, no copy as with method
#
#     :param expr: parser to set resultsname
#     :param name: resultsname
#     :param listAllMatches: whether strings matches should all be listed, or only last match should be kept
#     """
#     if name.endswith("*"):
#         name = name[:-1]
#         listAllMatches=True
#     expr.resultsName = name
#     expr.modalResults = not listAllMatches


def workaround_linestartend(string, linestart="<START>", lineend="<END>"):
    """ This is a workaround to handle more complex grammar with Linestart and Lineend being crucial.

    The current implementation of pyparsing has bugs concerning the native Linestart() and Lineend() objects.
    This simply replaces start and end with unique identifiers which afterwards can be used as if Linestart() / Lineend()
    would work directly.

    .. warning::
        lineend EOL is no WhiteSpace any longer and won't be skipped automatically any longer

    :param string: string to be translated
    :param linestart: identifier for new linestart
    :param lineend: identifier for new lineend
    :return: (translated string, expr to match start of line, expr to match end of line, expr to match rest of line)
    """
    repl_start = LineStart().leaveWhitespace().setParseAction(lambda : linestart)
    repl_end = LineEnd().leaveWhitespace().setParseAction(lambda : lineend)
    rest = SkipTo(LineEnd()).leaveWhitespace()
    repl_start_end = repl_start + rest + repl_end #cannot replace them separately because some bugs

    string_repl = repl_start_end.transformString(string)
    # additionally delete empty lines as they are usually regarded as whitespace and skipped accordingly
    repl_emptyline = Literal(linestart+lineend).suppress()
    string_repl = repl_emptyline.transformString(string_repl)

    SOL = Literal(linestart).suppress()
    EOL = Literal(lineend).suppress()
    ROL = SkipTo(lineend) + EOL  # rest of line

    return string_repl, SOL, EOL, ROL

def workaround_backtransform(string, SOL, EOL):
    """ revers of workaround_linestartend to again visualize strings in native way with linebreaks instead of identifiers

    :param string: string to be backtransformed
    :param SOL: expr to match start of line
    :param EOL: expr to match end of line
    :return: back transformed string
    """
    return Combine(EOL + SOL).setParseAction(lambda: "\n").transformString(string)


class Delim(Suppress):
    """ simple wrapper class to support easier construction of delimited lists
    """
    def __init__(self, delim):
        """ Wraps pyparsing.Suppress

        :param delim: delimiter =)
        :return: Delim
        """
        self.delim = delim
        super(Delim,self).__init__(delim)

    def __str__(self):
        return "'{}'".format(self.delim)

    def join(self, list_of_expr):
        """ concatinates given ``list_of_expr`` with intermediate Delim

        :param list_of_expr: list to be joined. Can also be a generator
        :return: list_of_expr[0] + Delim + list_of_expr[1] + Delim + ...
        """
        # return reduce(lambda a,b: a + self + b, list_of_expr)  # even faster than version below, however breaks for max recursion depth
        def gen():
            h = iter(list_of_expr)
            yield next(h)
            for r in h:
                yield self + r
        return And(gen())


def FastRepeat(expr, min=0, max=None):
    if min==max==0:
        return None
    elif min==max==1:
        return expr #nothing to do
    elif min==max:
        return And(expr for _ in xrange(max))
    elif min==0 and max==1:
        return Optional(expr)
    else:
        return Repeat(expr, min, max)