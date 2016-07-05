#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Felpers for the OS. Paths, files, ..."""
from __future__ import print_function, division
import re
import sys, shutil, os, subprocess
import platform

__author__ = 'Stephan Sahm <Stephan.Sahm@gmx.de>'


# paths
# =====

def abspath(p):
    return os.path.abspath(os.path.expanduser(p))


def ensure_endswith_sep(path):
    if not path.endswith(os.path.sep):
        return path + os.path.sep
    else:
        return path


# Windows
# -------

if platform.system() == "Windows":
    from wmi import WMI
    device = re.compile("[A-Z]:")
    mounts = {d.DeviceId: d.ProviderName for d in WMI().Win32_LogicalDisk()}


def replace_unc(path):
    if platform.system() != "Windows":
        return path

    drive, everythingelse = os.path.splitdrive(path)
    everythingelse = everythingelse[1:]  # for some weird reasons the split drive command does not remove \\ in front of everythingelse
    if device.match(drive):
        return os.path.join(mounts[drive] + os.path.sep, everythingelse)
    return path


# files
# =====

def load(filename):
    """ convenience function to easily load file

    :param filename: filename to load
    :return: string content of ``filename``
    """
    with open(filename) as f:
        return f.read()


def manipulate_file(string_manipulater, file_path, *args, **kwargs):
    """ filepath gets first argument of string_manipulater, *args, **kwargs
    can pass all other arguments

    Shall be used like working strings.
    Instead of ``string_manipulater(string, *args, **kwargs)``
    The syntax gets kind of``string_manipulater, file, *args, **kwargs``
    """
    file_dir, file_fn = os.path.split(file_path)
    shutil.copy(file_path, os.path.join(file_dir, ".%s.bak" % file_fn))  # security copy
    with open(file_path, "r") as f:
        data = f.read()
    with open(file_path, "w") as f:
        f.write(string_manipulater(data, *args, **kwargs))


def open_by_default_application(filepath):
    if sys.platform.startswith('darwin'):
        subprocess.call(('open', filepath))
    elif os.name == 'nt':
        os.startfile(filepath)
    elif os.name == 'posix':
        subprocess.call(('xdg-open', filepath))


#: copied from https://github.com/getify/JSON.minify/blob/python/json_minify/__init__.py
def json_minify(string, strip_space=True):
    tokenizer = re.compile('"|(/\*)|(\*/)|(//)|\n|\r')
    end_slashes_re = re.compile(r'(\\)*$')

    in_string = False
    in_multi = False
    in_single = False

    new_str = []
    index = 0

    for match in re.finditer(tokenizer, string):

        if not (in_multi or in_single):
            tmp = string[index:match.start()]
            if not in_string and strip_space:
                # replace white space as defined in standard
                tmp = re.sub('[ \t\n\r]+', '', tmp)
            new_str.append(tmp)

        index = match.end()
        val = match.group()

        if val == '"' and not (in_multi or in_single):
            escaped = end_slashes_re.search(string, 0, match.start())

            # start of string or unescaped quote character to end string
            if not in_string or (escaped is None or len(escaped.group()) % 2 == 0):  # noqa
                in_string = not in_string
            index -= 1  # include " character in next catch
        elif not (in_string or in_multi or in_single):
            if val == '/*':
                in_multi = True
            elif val == '//':
                in_single = True
        elif val == '*/' and in_multi and not (in_string or in_single):
            in_multi = False
        elif val in '\r\n' and not (in_multi or in_string) and in_single:
            in_single = False
        elif not ((in_multi or in_single) or (val in ' \r\n\t' and strip_space)):  # noqa
            new_str.append(val)

    new_str.append(string[index:])
    return ''.join(new_str)
