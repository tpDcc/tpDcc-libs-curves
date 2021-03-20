#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tpDcc-libs-curves function core implementations
"""

from __future__ import print_function, division, absolute_import

import os
import logging

from tpDcc.core import reroute
from tpDcc.managers import configs
from tpDcc.libs.python import python, fileio, jsonio, path as path_utils

from tpDcc.libs.curves.core import consts

logger = logging.getLogger(consts.LIB_ID)


def iterate_curve_root_paths():
    """
    Returns generator that iterates the locations where shape files can be located
    :return: generator(str)
    """

    all_curves_paths = list()
    shape_lib_config = configs.get_library_config('tpDcc-libs-curves')
    if shape_lib_config:
        curve_paths = shape_lib_config.get('curve_paths')
        curve_paths = python.force_list(curve_paths)
        all_curves_paths.extend(curve_paths)

    curve_paths = os.environ.get(consts.LIB_ID.replace('-', '_').upper(), '').split(os.pathsep)
    all_curves_paths.extend(curve_paths)

    all_curves_paths = list(set(all_curves_paths))
    for curve_path in all_curves_paths:
        if not curve_path or not os.path.isdir(curve_path):
            continue
        yield path_utils.clean_path(curve_path)


def iterate_curve_files(curves_path=None):
    """
    Iterator function that loops over all root curve files found in curves paths
    :param curves_path: str
    :return: generator(str)
    """

    if curves_path and os.path.isdir(curves_path):
        paths_to_find = [curves_path]
    else:
        paths_to_find = iterate_curve_root_paths()

    for curve_path in paths_to_find:
        for root_dir, _, filenames in os.walk(curve_path):
            for file_name in filenames:
                if file_name.endswith(consts.CURVE_EXT):
                    yield path_utils.clean_path(os.path.join(root_dir, file_name))


def iterate_available_curve_names(curves_path=None):
    """
    Iterator function that loop over all available curves names found in curves paths
    :param curves_path: str
    :return: generator(str)
    """

    for curve_path in iterate_curve_files(curves_path):
        yield os.path.splitext(os.path.basename(curve_path))[0]


def get_curve_names(curves_path=None):
    """
    Returns a list of all available curves names found in curves paths
    :param curves_path: str
    :return: list(str)
    """

    return list(iterate_available_curve_names(curves_path))


def find_curve_path_by_name(curve_name, curves_path=None):
    """
    Returns the absolute curve path with the given name
    :param curve_name: str, name of the curve to find
    :param curves_path: str
    :return: str
    """

    for curve_path in iterate_curve_files(curves_path=curves_path):
        split_name = os.path.splitext(os.path.basename(curve_path))
        if split_name[0] == curve_name:
            return curve_path

    return None


def load_curve_from_name(curve_name, curves_path=None):
    """
    Loads the curve data of the given curve by its name
    :param curve_name: str, name of the curve to load
    :param curves_path: str
    :return: dict, dictionary containing curve data
    """

    if curves_path and os.path.isdir(curves_path):
        curve_path = None
        for root_dir, _, filenames in os.walk(curves_path):
            if curve_path:
                break
            for file_name in filenames:
                if file_name.endswith(consts.CURVE_EXT) and file_name:
                    curve_path = path_utils.clean_path(os.path.join(root_dir, file_name))
                    break
    else:
        curve_path = find_curve_path_by_name(curve_name)

    if not curve_path:
        logger.warning('Curve with name "{}" does not exists!'.format(curve_path))
        return None

    return load_curve_from_path(curve_path)


def load_curve_from_path(curve_path):
    """
    Loads the curve data from the given curve path
    :param curve_path: str, path that stores curve data
    :return: dict, dictionary containing curve data
    """

    if not curve_path or not os.path.isfile(curve_path):
        return None
    path_ext = os.path.splitext(os.path.basename(curve_path))[0]
    if not path_ext != consts.CURVE_EXT:
        return None

    curve_data = jsonio.read_file(curve_path)

    return curve_data


def load_curves(curves_path=None):
    """
    Loads all the curves located in the given curves path
    :param curves_path: str, path where curves are located. If not given, first curve path found will be used
    :return:
    """

    if not curves_path or not os.path.isdir(curves_path):
        curves_path = list(iterate_curve_root_paths())
        if not curves_path:
            return None
        curves_path = curves_path[0]
    if not curves_path or not os.path.isdir(curves_path):
        return False

    curves_data = list()
    for root_dir, _, filenames in os.walk(curves_path):
        for file_name in filenames:
            if file_name.endswith(consts.CURVE_EXT):
                curve_data = load_curve_from_path(path_utils.clean_path(os.path.join(root_dir, file_name)))
                if not curve_data:
                    continue
                curves_data.append(curve_data)

    return curves_data


def save_curve(curve_node, curve_name, curves_path=None, override=True, save_matrix=False, normalize=True):
    """
    Saves the given curve transform node shapes into the given directory path
    :param curve_node: str
    :param curve_name: str
    :param curves_path: str
    :param override: bool
    :param save_matrix: bool
    :param normalize: bool
    :return:
    """

    if not curves_path or not os.path.isdir(curves_path):
        curves_path = list(iterate_curve_root_paths())
        if not curves_path:
            logger.warning('Impossible to save curve because no path to save curve defined')
            return False
        curves_path = curves_path[0]
    if not curves_path or not os.path.isdir(curves_path):
        logger.warning(
            'Impossible to save curve because path to save curve into does not exists: "{}"'.format(curves_path))
        return False

    curve_file_name = curve_name
    if not curve_name.endswith(consts.CURVE_EXT):
        curve_file_name = '{}{}'.format(curve_name, consts.CURVE_EXT)

    if not override and curve_file_name in get_curve_names():
        logger.warning('Curve name: "{}" already exists in curves paths'.format(curve_name))
        return None, None

    curve_data = serialize_curve(curve_node, normalize=normalize)
    if not save_matrix:
        for curve_shape in curve_data:
            curve_data[curve_shape].pop('matrix', None)

    curve_path = path_utils.clean_path(os.path.join(curves_path, curve_file_name))

    jsonio.write_to_file(curve_data, curve_path)

    return curve_data, curve_path


def save_curve_from_data(curve_data, curve_name, curves_path=None, override=True):
    """
    Saves the given curve data into the given directory path
    :param curve_data: dict
    :param curve_name: str
    :param curves_path: str
    :param override: bool
    :return:
    """

    if not curves_path or not os.path.isdir(curves_path):
        curves_path = list(iterate_curve_root_paths())
        if not curves_path:
            logger.warning('Impossible to save curve because no path to save curve defined')
            return False
        curves_path = curves_path[0]
    if not curves_path or not os.path.isdir(curves_path):
        logger.warning(
            'Impossible to save curve because path to save curve into does not exists: "{}"'.format(curves_path))
        return False

    curve_file_name = curve_name
    if not curve_name.endswith(consts.CURVE_EXT):
        curve_file_name = '{}{}'.format(curve_name, consts.CURVE_EXT)

    if not override and curve_file_name in get_curve_names():
        logger.warning('Control name: "{}" already exists in curves paths'.format(curve_name))
        return None, None

    curve_path = path_utils.clean_path(os.path.join(curves_path, curve_file_name))

    jsonio.write_to_file(curve_data, curve_path)

    return curve_data, curve_path


def rename_curve(curve_name, new_name, curves_path=None):
    """
    Renames the curve from the library with the new name
    :param curve_name: str, name of the curve without extension
    :param new_name: str, new name for the curve
    :param curves_path: str, directory path we want to rename the curve from
    :return:
    """

    if not curves_path or not os.path.isdir(curves_path):
        curve_path = find_curve_path_by_name(curve_name)
    else:
        curve_path = os.path.join(curves_path, '{}{}'.format(curve_name, consts.CURVE_EXT))
    if not curve_path or not os.path.isfile(curve_path):
        logger.warning('Curve file could not be renamed because it does not exists! "{}"'.format(curve_path))
        return False

    curve_directory = os.path.dirname(curve_path)
    curve_file_name = '{}{}'.format(curve_name, consts.CURVE_EXT)
    new_name = '{}{}'.format(new_name, consts.CURVE_EXT)
    new_curve_path = path_utils.clean_path(os.path.join(curve_path, new_name))
    if os.path.isfile(new_curve_path):
        logger.warning(
            'Cannot rename curve, because a curve with the same path already exists: "{}"'.format(new_curve_path))
        return False

    renamed_path = fileio.rename_file(curve_file_name, curve_directory, new_name)
    if not os.path.isfile(renamed_path):
        logger.warning('Was not possible to rename curve "{}" file: "{}'.format(curve_name, curve_path))
        return False

    logger.info(
        'Curve "{}" has been renamed successfully: "{}" >> "{}"'.format(curve_name, curve_path, renamed_path))

    return True


def delete_curve(curve_name, curves_path=None):
    """
    Renames the curve from the library. If not path given, all paths will be checked to find the curve
    :param curve_name: str, the name of the curve without extension
    :param curves_path: str, directory path where we want to curve the curve from
    """

    if not curves_path or not os.path.isdir(curves_path):
        curve_path = find_curve_path_by_name(curve_name)
    else:
        curve_path = os.path.join(curves_path, '{}{}'.format(curve_name, consts.CURVE_EXT))
    if not curve_path or not os.path.isfile(curve_path):
        logger.warning('Curve file could not be deleted because it does not exists! "{}"'.format(curve_path))
        return False

    curve_path = path_utils.clean_path(curve_path)
    fileio.delete_file(curve_path)
    if os.path.isfile(curve_path):
        logger.warning('Was not possible to remove curve "{}" file: "{}'.format(curve_name, curve_path))
        return False

    logger.info('Curve "{}" has been deleted successfully: "{}"'.format(curve_name, curve_path))

    return True


def create_curve(
        curve_type, curves_path=None, curve_name='new_curve', curve_size=1.0, translate_offset=(0.0, 0.0, 0.0),
        scale=(1.0, 1.0, 1.0), axis_order='XYZ', mirror=None, color=None, parent=None):
    """
    Creates the curve stored in the given path
    :param curve_type: str, type of the control to create
    :param curves_path: str, path that stores control data
    :param curve_name: str, name of the transform node of the created control
    :param curve_size: float, global size of the curve
    :param translate_offset: tuple(float, float, float), XYZ translation offset to apply to the curve
    :param scale: tuple(float, float, float), XYZ scale to apply to the curve
    :param axis_order: str, axis order of the curve. Default is XYZ.
    :param mirror: str or None, axis mirror to apply to the curve shapes (None, 'X', 'Y' or 'Z')
    :param color: tuple(float, float, float) or int, color of the curve
    :param parent: str or None, if given control shapes will be parented into this transform
    :return:
    """

    if not curves_path or not os.path.isdir(curves_path):
        control_path = find_curve_path_by_name(curve_type)
    else:
        control_path = os.path.join(curves_path, '{}{}'.format(curve_type, consts.CURVE_EXT))
    if not control_path or not os.path.isfile(control_path):
        return None

    control_data = jsonio.read_file(control_path, as_ordered_dict=True)
    if not control_data:
        return None

    return create_curve_from_data(
        control_data, name=curve_name, curve_size=curve_size, translate_offset=translate_offset, scale=scale,
        axis_order=axis_order, mirror=mirror, color=color, parent=parent)


@reroute.reroute_factory(consts.LIB_ID, 'curveslib')
def create_curve_from_data(curve_data, **kwargs):
    """
    Creates a new curve from the given curve data
    :param curve_data: dict
    :return:
    """

    raise NotImplementedError('Function create_control_from_data not implemented for current DCC!')


@reroute.reroute_factory(consts.LIB_ID, 'curveslib')
def get_curve_data(curve_shape_node, space=None, color_data=False):
    """
    Returns curve data from the given curve shape object
    :param curve_shape_node: MObject
    :param space: MSpace, space we want to retrieve curve data from
    :param color_data: bool, Whether to return or not color data of the curve
    :return: dict
    """

    raise NotImplementedError('Function get_curve_data not implemented for current DCC!')


@reroute.reroute_factory(consts.LIB_ID, 'curveslib')
def get_curve_data_from_transform(transform_node, space=None, color_data=False):
    """
    Returns curve data from the given curve shape object
    :param transform_node: MObject
    :param space: MSpace, space we want to retrieve curve data from
    :param color_data: bool, Whether to return or not color data of the curve
    :return: dict
    """

    raise NotImplementedError('Function get_curve_data_from_transform not implemented for current DCC!')


@reroute.reroute_factory(consts.LIB_ID, 'curveslib')
def serialize_curve(curve_node, normalize=True, **kwargs):
    """
    Returns dictionary that contains all information for rebuilding given NURBS curve
    :param curve_node: str, name of the curve to serialize
    :param normalize: periodic, bool
    :return: dict
    """

    raise NotImplementedError('Function serialize_curve not implemented for current DCC!')
