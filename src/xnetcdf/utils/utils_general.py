"""General utilities."""

import sys
from os.path import expanduser, expandvars

import numpy as np

# Ignore netCDF internal attributes
_IGNORED_ATTRS = {
    "CLASS",
    "NAME",
    "REFERENCE_LIST",
    "DIMENSION_LIST",
    "DIMENSION_LABELS",
    "_ARRAY_DIMENSIONS",
}
_IGNORED_PREFIXES = ("_Netcdf4", "_nc", "_NC")


class NetCDFError(Exception):
    """Error raised when dataset can't be viewed as netCDF."""

    pass


def get_dataset_name_and_protocol(dataset):
    """Get the data name and file system protocol.

    :Returns:

        (`object`, `str`, `str`)
            The input *dataset* object (but if it's a string, modifed
            with tilde and environment variable expansions), the
            dataset name, and the file system protocol of the
            dataset. If either of the latter two can not be
            determined, then ``''`` and ``-1`` are returned
            repectively.

    """
    dataset_name = ""
    protocol = -1

    try:
        dataset = expanduser(expandvars(dataset))
    except Exception:
        try:
            # fsspec file-like
            dataset_name = dataset.path
        except AttributeError:
            try:
                # BinaryIO
                dataset_name = dataset.name
            except AttributeError:
                try:
                    # fsspec Kerchunk dictionary-like
                    dataset_name = dataset.fs.storage_options.get("fo")
                except AttributeError:
                    pass
            else:
                # BinaryIO
                protocol = "file"
        else:
            try:
                # fsspec file-like
                protocol = dataset.fs.protocol
            except AttributeError:
                pass

        if not isinstance(dataset_name, str):
            dataset_name = str(dataset_name)

        if not dataset_name:
            dataset_name = "<file-or-directory-like>"

    else:
        # string-like
        from urllib.parse import urlparse

        dataset_name = dataset
        protocol = urlparse(dataset_name).scheme

    return dataset, dataset_name, protocol


def get_library(obj):
    """Get the library that provides an object.

    :Parameters:

        obj:
            The object (e.g. a `pyfive.File` instance),

    :Returns:

            The library (e.g. a `pyfive`).

    """
    module_name = type(obj).__module__
    parts = module_name.split(".")

    current_package = sys.modules.get(parts[0])
    if current_package is not None:
        return current_package

    # Try something else
    for i in range(1, len(parts) + 1):
        name = ".".join(parts[:i])
        mod = sys.modules.get(name)

        # If the module exists and has a __path__ then it's a package
        if mod and hasattr(mod, "__path__"):
            current_package = mod
        else:
            # We hit a module (file) or something not in
            # `sys.modules` => the previous 'current_package' was our
            # deepest package.
            break

    if current_package is None:
        # Fallback to the root if no deeper package was identified
        current_package = sys.modules.get(parts[0])

    return current_package


def format_attr(attr, value, library):
    """Format an attribute according to netCDF-4.

    :Parameters:

        attr: `str`
            The name of the attribute.

        value:
            The raw attribute value.

        library:
            The backend library that created the variable or group
            that owns the attribute value.

    :Returns:

            The formatted attribute value according to netCDF-4.

    """
    # Handle strings/bytes immediately
    if isinstance(value, (bytes, np.bytes_)):
        return value.decode("utf-8")

    try:
        if isinstance(value, library.Empty):
            dtype = value.dtype
            if dtype.kind in "SUT":
                return ""

            return np.array([], dtype=value)
    except AttributeError:
        pass

    if isinstance(value, str):
        return value

    if np.isscalar(value):
        return value

    # A Python or numpy sequence attribute
    is_numpy = False
    try:
        size = value.size  # Works for numpy
        is_numpy = True
    except AttributeError:
        try:
            size = len(value)  # Works for lists
        except TypeError:
            return value

    # Empty sequence
    if not size:
        if isinstance(value, (bytes, str)) or (
            isinstance(value, np.ndarray) and value.dtype.kind in "SUT"
        ):
            return ""

        return value

    if is_numpy:
        item = value.flat[0]
    else:
        item = value[0]

    # Single-element sequence
    if size == 1:
        # If size == 1 and it's an array, then treat it as a scalar.
        if isinstance(item, (bytes, np.bytes_)):
            # Return as a string
            return item.decode("utf-8")

        # Return as a numpy scalar
        if is_numpy:
            return item

        return getattr(value, "dtype", np.array(item).dtype).type(item)

    # Multi-element sequence: Return as a numeric numpy array, or as a
    # list of strings.

    # String sequence
    if isinstance(item, (bytes, np.bytes_)):
        return [v.decode("utf-8") for v in value]

    if isinstance(item, str):
        return list(value)

    # Numeric sequence
    if is_numpy:
        return value

    return np.array(value)


def parse_attributes(obj, raw_attrs):
    """Format raw attributes attributes according to netCDF-4.

    * Strings return as pure Python strings.
    * Single numeric values return as true numpy scalars (preserving
      data type).
    * Multi-element numeric values return as numpy arrays.
    * Multi-element string values return as Python lists.

    Attributes from the `_IGNORED_ATTRS` list, or which start with any
    of the `_IGNORED_PREFIXES`, are not returned.

    The attribues are sorted lexigraphically.

    :Parameters:

        obj: `Group` or `Variable`
            The object that owns the raw attributes.

        raw_attrs: `dict`
            The raw attributes from the dataset.

    :Returns:

        `dict`
            The attributes formatted according to netCDF-4.

    """
    library = obj.backend_library

    return {
        k: format_attr(k, v, library)
        for k, v in sorted(raw_attrs.items())
        if k not in _IGNORED_ATTRS and not k.startswith(_IGNORED_PREFIXES)
    }


def get_dimensions_from_defining_group(variable, dimension_names):
    """Get the source `Dimension` objects for a variable.

    For each given dimension name, find the corresponding `Dimension`
    object by searching up through the group hierarchy, starting from
    the variable's parent group.

    :Parameters:

        variable: `Variable`
            The variable for which  the dimensions are being sought.

        dimension_names: sequence of `str`
            The names of the dimensions to find.

    :Returns:

        `list` of `Dimension`
            The located `Dimension` objects.

    """
    dims = []
    for name in dimension_names:
        # Walk up the group tree towards the root group to find the
        # source groups where the dimension is defined
        current_group = variable.parent
        found = False
        while current_group is not None:
            dim = current_group.dimensions.get(name)
            if dim is not None:
                dims.append(dim)
                found = True
                break

            current_group = current_group.parent

        if not found:
            raise NetCDFError(
                f"Dimension {name!r} not found in the {variable.backend!r} "
                "group hierarchy."
            )

    return dims
