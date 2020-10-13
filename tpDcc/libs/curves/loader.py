#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for tpDcc.libs.curves
"""

import os

import tpDcc as tp
from tpDcc.core import command


def init(*args, **kwargs):
    """
    Initializes library
    :param dev: bool, Whether tpDcc-libs-qt is initialized in dev mode or not
    """

    runner = command.CommandRunner()
    if not runner:
        return

    commands_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'dccs', tp.Dcc.get_name(), 'commands')
    if not os.path.isdir(commands_path):
        return

    runner.manager().register_path(commands_path, package_name='tpDcc')
