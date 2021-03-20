#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains library definition for tpDcc-libs-curveslib
"""

from __future__ import print_function, division, absolute_import

import os
import logging.config

from tpDcc import dcc
from tpDcc.core import library, command
from tpDcc.libs.python import path as path_utils

from tpDcc.libs.curves.core import consts

logger = logging.getLogger(consts.LIB_ID)


class CurvesLib(library.DccLibrary, object):

    ID = consts.LIB_ID

    def __init__(self, *args, **kwargs):
        super(CurvesLib, self).__init__(*args, **kwargs)

    @classmethod
    def config_dict(cls):
        base_tool_config = library.DccLibrary.config_dict()
        tool_config = {
            'name': 'Curves Library',
            'id': CurvesLib.ID,
            'supported_dccs': {'maya': ['2017', '2018', '2019', '2020']},
            'tooltip': 'Library to manage curves in a DCC agnostic way',
            'root': cls.ROOT if hasattr(cls, 'ROOT') else '',
            'file': cls.PATH if hasattr(cls, 'PATH') else '',
        }
        base_tool_config.update(tool_config)

        return base_tool_config

    @classmethod
    def load(cls):
        # Initialize environment variable that contains paths were curves libs command are located
        # This environment variable is used by the command runner
        dcc_name = dcc.client().get_name()
        commands_path = path_utils.clean_path(
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dccs', dcc_name, 'commands'))
        if os.path.isdir(commands_path):
            command.CommandRunner().manager().register_path(commands_path, 'tpDcc')
