"""Utilities for the parsing HDF5 datasets."""

from .utils_general import NetCDFError


def hdf5_dimension_names(variable):
    """Get the variable dimension names.

    Raises a `NetCDFError` exception if the DIMENSION_LIST attribute
    is not appropriately set.

    :Parameters:

        variable: `Variable`
            The variable.

    :Returns:

        `tuple`
            The dimension names relative to their parent groups,
            e.g. ``('time', 'lat', 'lon')``.

    """
    var_attrs = variable._var_attrs

    # Case 1: It's a coordinate variable that has the same
    #         name as its dimension.
    if var_attrs.get("CLASS") == b"DIMENSION_SCALE":
        return (variable.name,)

    ndim = variable.ndim

    # Case 2: It's a scalar variable with no dimensions
    if not ndim:
        return ()

    # Case 3: It's an N-d variable (N>=1) not covered by
    #         case 1.
    dim_list = var_attrs.get("DIMENSION_LIST", ())
    if len(dim_list) != ndim:
        raise NetCDFError(
            f"Variable {variable.path!r} requires {ndim} "
            f"DIMENSION_LIST links, found {len(dim_list)}"
        )

    dim_names = []

    for ref in dim_list:
        try:
            if hasattr(ref, "item"):
                ref = ref.item()
            elif isinstance(ref, (list, tuple)) and len(ref) > 0:
                ref = ref[0]

            root_grp = variable.parent.root._grp
            dim_dataset = root_grp[ref]
            dim_names.append(dim_dataset.name.split("/")[-1])
        except (KeyError, ValueError, TypeError):
            continue

    return tuple(dim_names)


def hdf5_parse_group_structure(group):
    """Parse the group structure for the `pyfive` and `h5py` backends.

    Parses variables, dimensions, and sub-groups, recursively.

    :Parameters:

        group: `Group` or `Dataset`
            The group to be parsed.

    :Returns:

        `None`

    """
    raw_dims = {}
    subgroups = {}
    datasets = {}
    dataset_attrs = {}
    dataset_shape = {}

    # Categorise objects without double-reading items from the HDF5
    # dataset
    library = group.backend_library
    library_has_groups = hasattr(library, "Group")

    for name, h5 in group._grp.items():
        if library_has_groups and isinstance(h5, library.Group):
            subgroups[name] = h5
        else:
            # Everyhing else must be a Dataset
            datasets[name] = h5

    # Extract dimension scales (strictly ignoring scalars)
    for name, var in datasets.items():
        shape = var.shape
        attrs = var.attrs
        dataset_attrs[name] = attrs
        dataset_shape[name] = shape

        if shape and attrs.get("CLASS") == b"DIMENSION_SCALE":
            # Get ID: Use `None` if missing to push to end of sort
            dim_id = attrs.get("_Netcdf4Dimid")
            if dim_id is not None:
                dim_id = int(dim_id)

            dim_name = name.split("/")[-1]

            is_unlimited = False
            maxshape = var.maxshape
            if maxshape and len(maxshape) > 0:
                is_unlimited = maxshape[0] is None

            raw_dims[dim_name] = {
                "id": dim_id,
                "size": shape[0],
                "is_unlimited": is_unlimited,
                "is_stub": (
                    b"not a netCDF variable" in attrs.get("NAME", b"")
                ),
            }

    # Sort and create Dimension objects
    #
    # Sorting ensures consistency with netCDF4-python, which preserves
    # the creation order of its dimensions in an ordered dictionary.
    #
    # We sort by (ID, Name). If ID is `None` (pure HDF5), it's treated
    # as infinity tqo ensure it appears after the netCDF-indexed
    # dimensions.
    sorted_items = sorted(
        raw_dims.items(),
        key=lambda x: (
            x[1]["id"] if x[1]["id"] is not None else float("inf"),
            x[0],
        ),
    )

    for name, d_info in sorted_items:
        group._create_dimension(name, d_info["size"], d_info["is_unlimited"])

    # Create variables (skipping internal netCDF stubs)
    for name, var in datasets.items():
        dim_name = name.split("/")[-1]

        # If it's in 'raw_dims' and flagged as a stub then skip
        # it. Otherwise - whether it's a coordinate variable, normal
        # data, or a scalar pretending to be a scale - it becomes a
        # Variable.
        is_stub = raw_dims.get(dim_name, {}).get("is_stub", False)

        if not is_stub:
            group._create_variable(
                name, var, dataset_attrs[name], shape=dataset_shape[name]
            )

    # ----------------------------------------------------------------
    # Recursively create subgroups
    # ----------------------------------------------------------------
    for name, grp in subgroups.items():
        group._create_group(name, grp, grp.attrs)
