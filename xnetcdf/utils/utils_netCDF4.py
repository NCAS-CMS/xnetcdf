"""Utilities for the `netCDF4` backend."""

from .utils_general import get_dataset_name_and_protocol, get_library


def netCDF4_parse_group_structure(group):
    """Parse the group structure for the `netCDF4` backend.

    Parses variables, dimensions, and sub-groups, recursively.

    :Parameters:

        group: `Group` or `Dataset`
            The group to be parsed.

    :Returns:

        `None`

    """
    # Create dimensions in this group
    for name, dim in group._grp.dimensions.items():
        group._create_dimension(name, dim.size, dim.isunlimited())

    # Create variables in this group
    for name, var in group._grp.variables.items():
        attrs = {attr: var.getncattr(attr) for attr in var.ncattrs()}
        group._create_variable(name, var, attrs)

    # Recursively create subgroups
    for name, grp in group._grp.groups.items():
        attrs = {attr: grp.getncattr(attr) for attr in grp.ncattrs()}
        group._create_group(name, grp, attrs)


def netCDF4_read(dataset, options):
    """Read a dataset with `netCDF4`.

    The dataset is opened with "auto mask" and "auto scale" both set
    to `False`.

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
            Additional keyword parameters to pass to
            `netCDF4.Dataset`.

    :Returns:

        (`netCDF4.Dataset`, `dict`, library)
            The opened dataset, the dataset's global attributes, and
            the `netCDF4` library itself.

    """
    import netCDF4

    dataset_name = ""
    protocol = -1

    if isinstance(dataset, netCDF4.Dataset):
        nc = dataset
        library = get_library(dataset)
        owns_accessor = False

        dataset_name = dataset.filepath()
        if not dataset_name:
            dataset_name = "<netCDF4-like>"
        else:
            try:
                from urllib.parse import urlparse

                protocol = urlparse(dataset_name).scheme
            except Exception:
                pass

    else:
        options = options.copy()
        mode = options.pop("mode", "r")
        if mode != "r":
            raise ValueError(f"Can't set mode={mode!r} in netCDF4_options")

        dataset, dataset_name, protocol = get_dataset_name_and_protocol(
            dataset
        )

        nc = netCDF4.Dataset(dataset, mode="r", **options)
        nc.set_auto_maskandscale(False)

        library = netCDF4
        owns_accessor = True

    return {
        "dataset_name": dataset_name,
        "protocol": protocol,
        "nc": nc,
        "attrs": {attr: nc.getncattr(attr) for attr in nc.ncattrs()},
        "backend_api": "netCDF4",
        "library": library,
        "owns_accessor": owns_accessor,
    }
