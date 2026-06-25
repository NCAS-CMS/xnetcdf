"""Utilities for the `netcdf_file` backend."""

from .utils_general import get_dataset_name_and_protocol, get_library


def netcdf_file_close(root):
    """Close the dataset opened with `netcdf_file`.

    It is assumed, but not checked, that the backend is indeed
    `netcdf_file`.

    :Parameters:

        root: `Dataset`
            The root group.

    :Returns:

        `None`

    """
    # We can't close a scipy.io.netcdf_file instance opened with
    # mmap=True when any variable still exists, or when an array
    # referring to a variable's data still exists (see
    # scipy.io.netcdf_file docs for details). So, rather than
    # attempting to hunt down all such references (messy!), the hack
    # of setting the '_mm_buf' attribute to `None` allows the file to
    # be closed. We get away with this because we know that we've
    # copied all memory mapped data into memory inside
    # `Variable.__getitem__`.
    root._grp._mm_buf = None

    root._grp.close()


def netcdf_file_dtype(variable):
    """The data type of variable opened with `netcdf_file`.

    :Parameters:

        variable: `Variable`
            The variable.

    :Returns:

        `numpy.dtype`

    """
    return variable._var[(slice(0, 1),) * len(variable.shape)].flat[0].dtype


def netcdf_file_read(dataset, options):
    """Read a dataset with `scipy.io.netcdf_file`.

    The dataset is opened with `scipy.io.netcdf_file` options
    ``mode='r'`` and ``mmap=True``.

    :Parameters:

        dataset:
            The definition of the dataset to be read. One of:

            * string-like (such as `str` or `pathlib.Path`)
            * file-like (such as `io.BufferedReader` or the result
                         of an `fsspec` file system open)
            * directory-like (such as `fsspec.mapping.FSMap`)

             An exception is raised if the *dataset* can't be
             interpreted.

        options: `dict`
            Additional keyword parameters to pass to `netcdf_file`.

    :Returns:

        (`scipy.io.netcdf_file`, `dict`, library)
            The opened dataset, the dataset's global attributes, and
            the `netcdf_file` library itself.

    """
    from scipy.io import netcdf_file

    dataset_name = ""
    protocol = -1

    if isinstance(dataset, netcdf_file):
        nc = dataset
        library = get_library(dataset)
        owns_accessor = False

        dataset_name = dataset.filename
        if not dataset_name:
            dataset_name = "<netcdf_file-like>"
        else:
            try:
                from urllib.parse import urlparse

                protocol = urlparse(dataset_name).scheme
            except Exception:
                pass

    else:
        options = options.copy()
        mode = options.pop("mode", "r")
        mmap = options.pop("mmap", True)
        if mode != "r":
            raise ValueError(f"Can't set mode={mode!r} in netcdf_file_options")

        if not mmap:
            raise ValueError("Can't set mmap=False in netcdf_file_options")

        dataset, dataset_name, protocol = get_dataset_name_and_protocol(
            dataset
        )
        nc = netcdf_file(dataset, mode="r", mmap=True, **options)

        library = netcdf_file
        owns_accessor = True

    return {
        "dataset_name": dataset_name,
        "protocol": protocol,
        "nc": nc,
        "attrs": nc._attributes,
        "backend_api": "netcdf_file",
        "library": library,
        "owns_accessor": owns_accessor,
    }


def netcdf_file_parse_group_structure(group):
    """Parse the group structure for the `netcdf_file` backend.

    Parses variables, dimensions in the root. There are no
    sub-groups in netCDF-3.

    :Parameters:

        group: `Group` or `Dataset`
            The group to be parsed.

    :Returns:

        `None`

    """
    # Create dimensions in this group
    for name, size in group._grp.dimensions.items():
        group._create_dimension(name, size, isunlimited=False)

    # Create variables in this group
    for name, var in group._grp.variables.items():
        group._create_variable(name, var, var._attributes)
