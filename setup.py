#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Stephan Sahm <Stephan.Sahm@gmx.de>'

import os
import shutil
from setuptools import setup
from distutils.command.clean import clean as Clean

class CleanCmd(Clean):

    description = "Cleans ..."

    def run(self):

        Clean.run(self)

        if os.path.exists('build'):
            shutil.rmtree('build')

        for dirpath, dirnames, filenames in os.walk('.'):
            for filename in filenames:
                if (filename.endswith('.so') or \
                    filename.endswith('.pyd') or \
                    filename.endswith('.pyc') or \
                    filename.endswith('_wrap.c') or \
                    filename.startswith('wrapper_') or \
                    filename.endswith('~')):
                        os.unlink(os.path.join(dirpath, filename))

            for dirname in dirnames:
                if dirname == '__pycache__' or dirname == 'build':
                    shutil.rmtree(os.path.join(dirpath, dirname))
                if dirname == "pymscons.egg-info":
                    shutil.rmtree(os.path.join(dirpath, dirname))

setup(
    name='schlichtanders',
    version='0.1',
    description='Personal collection of helper methods by schlichtanders',
    author=__author__,
    author_email='Stephan.Sahm@gmx.de',
    license='open source',
    packages=['schlichtanders'],
    zip_safe=False,
    install_requires=['numpy >= 1.10.2',
                      'matplotlib >= 1.3.1'],
    cmdclass={'clean': CleanCmd}
    )
