"""Utilities for the `xarray` backend."""

from .utils_general import get_dataset_name_and_protocol, get_library


def xarray_parse_group_structure(group):
    """Parse the group structure for the `xarray` backend.

    Parses variables, dimensions, and sub-groups, recursively.

    :Parameters:

        group: `Group` or `File`
            The group to be parsed.

    :Returns:

        `None`

    """
    # Create dimensions in this group ('grp' is an `xarray.DataTree`
    # instance)
    grp = group._grp

    # Find which dimensions are actually defined in this group, as
    # opposed to being copied from an ancestor group.
    maps = grp.sizes.mapping.maps
    local_map = maps[0]
    ancestor_maps = maps[1:]
    defined_dims = {
        name: size
        for name, size in local_map.items()
        if not any(name in m for m in ancestor_maps)
    }

    grp = grp.to_dataset(inherit=False)
    for name, size in defined_dims.items():
        unlimited = name in grp.encoding.get("unlimited_dims", ())
        group._create_dimension(name, size, unlimited)

    # Create variables in this group
    for name, var in grp.variables.items():
        group._create_variable(name, var, var.attrs)

    # Recursively create subgroups
    for name, grp in group._grp.children.items():
        group._create_group(name, grp, grp.attrs)


def xarray_read(dataset, options):
    """Read a dataset with `xarray`.

    The dataset is opened with `xarray.open_datatree` options
    ``mask_and_scale=False`` and ``decode_cf=False``.

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
            `xarray.open_datatree`. The keyword arguments
            ``mask_and_scale=False, decode_cf=False`` are always
            automatially applied, even when not provided in *options*,
            and can't be set to different values.

    :Returns:

        (`xarray.DataTree`, `dict`, library)
            The opened dataset, the dataset's global attributes, and
            the `xarray` library itself.

    """
    import xarray

    dataset_name = None
    protocol = -1

    if isinstance(dataset, (xarray.Dataset, xarray.DataTree)):
        if isinstance(dataset, xarray.Dataset):
            # Convert a Dataset to a DataTree
            dataset = xarray.DataTree(dataset=dataset)

        nc = dataset
        library = get_library(dataset)
        owns_accessor = False

        # Attempt to get the dataset name and file system protocol
        try:
            dataset_name = dataset.encoding.get("source")
        except AttributeError:
            pass

        if not dataset_name or not isinstance(dataset_name, str):
            dataset_name = "<xarray-like>"

    else:
        options = options.copy()
        mask_and_scale = options.pop("mask_and_scale", False)
        decode_cf = options.pop("decode_cf", False)
        if mask_and_scale:
            raise ValueError("Can't set mask_and_scale=True in xarray_options")

        if decode_cf:
            raise ValueError("Can't set decode_cf=True in xarray_options")

        if "chunks" not in options:
            options["chunks"] = "auto"

        dataset, dataset_name, protocol = get_dataset_name_and_protocol(
            dataset
        )
        nc = xarray.open_datatree(
            dataset, mask_and_scale=False, decode_cf=False, **options
        )

        library = xarray
        owns_accessor = True

    return {
        "dataset_name": dataset_name,
        "protocol": protocol,
        "nc": nc,
        "attrs": nc.attrs,
        "backend_api": "xarray",
        "library": library,
        "owns_accessor": owns_accessor,
    }
