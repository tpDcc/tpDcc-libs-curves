#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tpDcc-libs-curves function implementations for Maya
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp
from tpDcc.libs.python import python
import tpDcc.dccs.maya as maya
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
    parent = kwargs.get('parent', None)

    return curves.create_curve_shape(
        curve_data, curve_size=curve_size, translate_offset=translate_offset, scale=scale, axis_order=axis_order,
        mirror=mirror, parent=parent)


def get_curve_data(curve_shape_node, space=None, color_data=False):
    """
    Returns curve data from the given curve shape object
    :param curve_shape_node: MObject
    :param space: MSpace, space we want to retrieve curve data from
    :param color_data: bool, Whether to return or not color data of the curve
    :return: dict
    """

    if isinstance(curve_shape_node, maya.OpenMaya.MObject):
        curve_shape_node = maya.OpenMaya.MFnDagNode(curve_shape_node).getPath()

    data = api_node.get_node_color_data(curve_shape_node.node()) if color_data else dict()
    curve = api.NurbsCurveFunction(curve_shape_node.node())

    data.update({
        # 'knots': tuple(curve.get_knot_values()),
        'cvs': [cv[:-1] for cv in map(tuple, curve.get_cv_positions(space))],
        'degree': curve.get_degree(),
        'form': curve.get_form(),
        'matrix': tuple(api_node.get_world_matrix(curve.obj.object()))
    })
    # data['knots'] = tuple([float(i) for i in range(-data['degree'] + 1, len(data['cvs']))])

    return data


def serialize_curve(curve_node, space=None, degree=None, periodic=False, normalize=True):
    """
    Returns dictionary that contains all information for rebuilding given NURBS curve
    :param curve_node: str, name of the curve to serialize
    :param space: absolute_position, bool
    :param degree: degree, int
    :param periodic: bool
    :param normalize: bool, Whether or not curve CVs should be normalized to stay in 0 to 1 space
    :return: dict
    """

    space = space or maya.OpenMaya.MSpace.kObject

    if python.is_string(curve_node):
        curve_node = api_node.as_mobject(curve_node)

    data = dict()
    shapes = api_node.get_shapes(api.DagNode(curve_node).get_path(), filter_types=maya.OpenMaya.MFn.kNurbsCurve)
    for shape in shapes:
        dag_node = api.DagNode(shape.node())
        is_intermediate = dag_node.is_intermediate_object()
        if is_intermediate:
            continue
        data[maya.OpenMaya.MNamespace.stripNamespaceFromName(dag_node.get_name())] = get_curve_data(shape, space=space)
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

    if crv is None or not tp.Dcc.object_exists(crv):
        return False

    curve_shapes = tp.Dcc.get_curve_shapes(crv)

    return curve_shapes
