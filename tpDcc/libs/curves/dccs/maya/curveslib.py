#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tpDcc-libs-curves function implementations for Maya
"""

from __future__ import print_function, division, absolute_import

from collections import OrderedDict

import maya.api.OpenMaya

from tpDcc import dcc
from tpDcc.libs.python import python
from tpDcc.dccs.maya import api
from tpDcc.dccs.maya.api import curves, node as api_node


def create_curve_from_data(curve_data, **kwargs):
    """
    Creates a new curve
    :param curve_data: str, shape name from the dictionary
    """

    curve_size = kwargs.get('curve_size', 1.0)
    translate_offset = kwargs.get('translate_offset', (0.0, 0.0, 0.0))
    scale = kwargs.get('scale', (1.0, 1.0, 1.0))
    axis_order = kwargs.get('axis_order', 'XYZ')
    mirror = kwargs.get('mirror', None)
    color = kwargs.get('color', None)
    parent = kwargs.get('parent', None)

    return curves.create_curve_shape(
        curve_data, curve_size=curve_size, translate_offset=translate_offset, scale=scale, axis_order=axis_order,
        mirror=mirror, color=color, parent=parent)


def update_curve_from_data(transform_node, curve_data):
    """
    Updates given transform node shapes with the shapes stored in the given data dictionary
    :param transform_node: str
    :param curve_data: dict
    """

    pass


def get_curve_data(curve_shape_node, space=None, color_data=False, parent=None):
    """
    Returns curve data from the given curve shape object
    :param curve_shape_node: MObject or str
    :param space: MSpace, space we want to retrieve curve data from
    :param color_data: bool, Whether to return or not color data of the curve
    :param parent:
    :return: dict
    """

    return curves.get_curve_data(curve_shape_node, space=space, color_data=color_data, parent=parent)


def get_curve_data_from_transform(transform_node, space=None, color_data=False):
    """
    Returns curve data from the given curve shape object
    :param transform_node: MObject
    :param space: MSpace, space we want to retrieve curve data from
    :param color_data: bool, Whether to return or not color data of the curve
    :return: dict
    """

    transform_node = maya.api.OpenMaya.MFnDagNode(api_node.as_mobject(transform_node)).getPath()
    curves_data = curves.serialize_transform_curve(node=transform_node, space=space, color_data=color_data)

    return curves_data


def serialize_curve(curve_node, normalize=True, **kwargs):
    """
    Returns dictionary that contains all information for rebuilding given NURBS curve
    :param curve_node: str, name of the curve to serialize
    :param normalize: bool, Whether or not curve CVs should be normalized to stay in 0 to 1 space
    :return: dict
    """

    space = kwargs.pop('space', None) or maya.api.OpenMaya.MSpace.kObject

    if python.is_string(curve_node):
        curve_node = api_node.as_mobject(curve_node)

    data = OrderedDict()
    shapes = api_node.get_shapes(api.DagNode(curve_node).get_path(), filter_types=maya.api.OpenMaya.MFn.kNurbsCurve)
    for shape in shapes:
        dag_node = api.DagNode(shape.node())
        is_intermediate = dag_node.is_intermediate_object()
        if is_intermediate:
            continue
        data[maya.OpenMaya.MNamespace.stripNamespaceFromName(dag_node.get_name())] = get_curve_data(shape, space=space)
    children = api_node.get_child_transforms(api.DagNode(curve_node).get_path())
    for child in children:
        dag_node = api.DagNode(child.node())
        child_shapes = api_node.get_shapes(
            api.DagNode(child.node()).get_path(), filter_types=maya.api.OpenMaya.MFn.kNurbsCurve)
        for child_shape in child_shapes:
            shape_dag_node = api.DagNode(child_shape.node())
            is_intermediate = shape_dag_node.is_intermediate_object()
            if is_intermediate:
                continue
            data[maya.api.OpenMaya.MNamespace.stripNamespaceFromName(dag_node.get_name())] = get_curve_data(
                child_shape, space=space, parent=shapes[0].node() or curve_node)
    if not data:
        return

    # Normalize CVs to be in 0-1 space
    if normalize:
        mx = -1
        for shape_name, shape_data in data.items():
            for cv in shape_data['cvs']:
                for p in cv:
                    if mx < abs(p):
                        mx = abs(p)
        for shape_name, shape_data in data.items():
            shape_data['cvs'] = [[p / mx for p in pt] for pt in shape_data['cvs']]

    return data


def validate_curve(crv):
    """
    Returns whether the given name corresponds to a valid NURBS curve
    :param crv: str, name of the curve we want to check
    :return: bool
    """

    if crv is None or not dcc.node_exists(crv):
        return False

    curve_shapes = dcc.get_curve_shapes(crv)

    return curve_shapes
