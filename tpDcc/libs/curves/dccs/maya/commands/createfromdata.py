#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Dcc commands to create curves in Maya
"""

from __future__ import print_function, division, absolute_import

import maya.cmds
import maya.api.OpenMaya

from tpDcc.core import command
from tpDcc.libs.curves.core import curveslib
from tpDcc.dccs.maya.api import node as api_node


class CreateCurveFromData(command.DccCommand, object):

    id = 'tpDcc-libs-curves-dccs-maya-createCurveFromData'
    creator = 'Tomas Poveda'
    is_undoable = True

    _parent = None
    _new_parent = False
    _shape_nodes = list()

    def resolve_arguments(self, arguments):
        try:
            parent = arguments.parent
        except AttributeError:
            parent = None
        curve_data = arguments.curve_data
        if not curve_data:
            self.cancel('No curve data given')
        if parent is not None:
            handle = maya.api.OpenMaya.MObjectHandle(parent)
            if not handle.isValid() or not handle.isAlive():
                self.cancel('Parent no longer exists in current scene: "{}"'.format(parent))
            parent = handle
        else:
            self._new_parent = True

        arguments['parent'] = parent
        self._parent = parent

        return arguments

    def run(self, curve_data=None, curve_size=1.0, translate_offset=(0.0, 0.0, 0.0),
            scale=(1.0, 1.0, 1.0), axis_order='XYZ', mirror=None, parent=None):
        parent_mobj, shape_mobjs = curveslib.create_curve_from_data(
            curve_data, curve_size=curve_size, translate_offset=translate_offset,
            scale=scale, axis_order=axis_order, mirror=mirror, parent=parent)
        self._parent = maya.api.OpenMaya.MObjectHandle(parent_mobj)
        self._shape_nodes = map(maya.api.OpenMaya.MObjectHandle, shape_mobjs)

        return parent_mobj, shape_mobjs

    def undo(self):
        if self._new_parent:
            if self._parent.isValid() and self._parent.isAlive():
                maya.cmds.delete(api_node.name_from_mobject(self._parent.object()))
        elif self._shape_nodes:
            maya.cmds.delete([api_node.name_from_mobject(
                i.object()) for i in self._shape_nodes if (i.isValid() and i.isAlive())])
