#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tpDcc-libs-curves function implementations for 3ds Max
"""

from __future__ import print_function, division, absolute_import

from tpDcc import dcc
from tpDcc.core import consts
from tpDcc.dccs.max.core import curves


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

    curve_data_ = curve_data.copy()
    for curve_name, data in curve_data_.items():
        cvs = curve_data[curve_name]['cvs']
        up_axis = curve_data[curve_name].get('up_axis', consts.Axis.Y)
        if up_axis == consts.Axis.Y:
            new_cvs = [dcc.convert_translation(cv) for cv in cvs]
            curve_data[curve_name]['cvs'] = new_cvs

    for curve_name, data in curve_data_.items():
        cvs = curve_data[curve_name]['cvs']
        degree = curve_data[curve_name]['degree']
        order = degree + 1
        total_knots = order + len(cvs)
        while len(curve_data[curve_name]['knots']) < total_knots:
            curve_data[curve_name]['knots'].insert(0, curve_data[curve_name]['knots'][0])
            curve_data[curve_name]['knots'].append(curve_data[curve_name]['knots'][-1])

    return curves.create_curve_shape(
        curve_data, curve_size=curve_size, translate_offset=translate_offset, scale=scale, axis_order=axis_order,
        mirror=mirror, color=color)
