"""Utilities for the `zarr` backend."""

from .utils_general import (
    NetCDFError,
    get_dataset_name_and_protocol,
    get_library,
)


def zarr_get_dataset_name(z):
    """A standardized path from any Zarr v3 Group or Array.

    :Returns:

        `str`
             The path or URI, such as
             ``'/absolute/local/path/data.zarr'``,
             ``'s3://my-bucket/data.zarr'``,
             ``'https://example.com/data.zarr'``, ``'memory://'``.

    """
    import os

    from zarr.storage import (
        FsspecStore,
        LocalStore,
        MemoryStore,
        ObjectStore,
        ZipStore,
    )

    def join_paths(base, subpath):
        """Helper to join a base path and an internal node path."""
        if not subpath:
            return base.rstrip("/")

        return f"{base.rstrip('/')}/{subpath.lstrip('/')}"

    # Zarr v3 nodes have a .store_path wrapper containing the store
    # and internal node path
    store = z.store_path.store
    node_path = z.store_path.path or ""

    # Case 1: Standard local storage
    if isinstance(store, LocalStore):
        # store.root is a pathlib.Path or string representing the
        # absolute local directory
        base_path = os.path.abspath(str(store.root))
        return join_paths(base_path, node_path)

    # Case 2: Memory storage
    elif isinstance(store, MemoryStore):
        return join_paths("memory://", node_path)

    # Case 3: Zip archive storage
    elif isinstance(store, ZipStore):
        # store.path is the path to the physical .zip container file
        base_path = os.path.abspath(str(store.path))
        return f"zip://{join_paths(base_path, node_path)}"

    # Case 4: Fsspec-backed storage (S3, GCS, HTTP, etc.)
    elif isinstance(store, FsspecStore) or hasattr(store, "fs"):
        protocol = store.fs.protocol
        # fsspec protocol can sometimes be a tuple/list
        if isinstance(protocol, (tuple, list)):
            protocol = protocol[0]

        base_path = str(store.path)

        # Format based on whether it is a web protocol or a local file
        # protocol
        if protocol in ("file", "local"):
            return join_paths(os.path.abspath(base_path), node_path)

        return f"{protocol}://{join_paths(base_path, node_path)}"

    # Case 5: ObjectStore backends (rust obstore drivers)
    elif isinstance(store, ObjectStore) or hasattr(store, "_store"):
        # The internal obstore instance is held in store._store
        backend = store._store
        # e.g. 'HttpStore', 'S3Store', 'LocalFileSystem'
        backend_type = type(backend).__name__

        # Combine Zarr's prefix configuration with the specific array
        # node path
        store_prefix = getattr(store, "prefix", "")
        combined_subpath = join_paths(store_prefix, node_path)

        if backend_type == "HttpStore":
            base_url = getattr(backend, "base_url", "http://unknown")
            return join_paths(base_url, combined_subpath)

        elif backend_type == "S3Store":
            bucket = getattr(backend, "bucket", "unknown-bucket")
            return f"s3://{join_paths(bucket, combined_subpath)}"

        elif backend_type == "GoogleCloudStorage":
            bucket = getattr(backend, "bucket", "unknown-bucket")
            return f"gcs://{join_paths(bucket, combined_subpath)}"

        elif backend_type == "LocalFileSystem":
            # For native local object store, extract the path string
            base_path = getattr(backend, "root", "") or os.getcwd()
            return join_paths(
                os.path.abspath(str(base_path)), combined_subpath
            )

    # Case 6: Fallback for raw strings or customized stores
    path_str = str(z.store_path)

    # Clean up standard variations if the generic string started with
    # common wrappers
    if path_str.startswith("object_store://"):
        # If it leaked an unparsed string fallback from a custom
        # obstore structure
        parts = path_str.split("object_store://")[-1].split("/")
        return "/".join(parts[1:]) if len(parts) > 1 else path_str

    return path_str


def zarr_dimension_maps(group):
    """Populate the dimension map dictionaries in the root group.

    Stores the dimensions defined in *group* and all of its sub-groups
    recursively. For instance::

       {'/': {'bounds2': <xnetcdf.Dimension: /bounds2, size=2>},
        '/forecast': {'lon': <xnetcdf.Dimension: /forecast/lon, size=8, unlimited>},
        '/forecast/model': {'lat': <xnetcdf.Dimension: /forecast/model/lat, size=5>}}
        '/forecast/model2': {}}

    Stores the tuple of the dimensions for all variables in *group*
    and its sub-groups recursively. For instance::

       {'/forecast/lon': (<xnetcdf.Dimension: /forecast/lon, size=8, unlimited>,),
        '/forecast/lon_bnds': (<xnetcdf.Dimension: /forecast/lon, size=8, unlimited>,
                               <xnetcdf.Dimension: /bounds2, size=2>),
        '/forecast/model/lat': (<xnetcdf.Dimension: /forecast/model/lat, size=5>,),
        '/forecast/model/lat_bnds': (<xnetcdf.Dimension: /forecast/model/lat, size=5>,
                                     <xnetcdf.Dimension: /bounds2, size=2>),
        '/forecast/model/q': (<xnetcdf.Dimension: /forecast/model/lat, size=5>,
                              <xnetcdf.Dimension: /forecast/lon, size=8, unlimited>),
        '/forecast/model2/tas': (<xnetcdf.Dimension: /forecast/model/lat, size=5>,
                                 <xnetcdf.Dimension: /forecast/lon, size=8, unlimited>),
        '/time': ()}

    :Parameters:

        group: `Group`
            The group object.

    :Returns:

        `None`

    """
    group_path = group.path
    root = group.root
    group_to_dims = root._group_to_dims
    variable_to_dims = root._variable_to_dims
    group_dimension_search = root._zarr_dimension_search

    # Initialise the mapping from this group to its `Dimension`
    # objects. Use 'setdefault' because a previous call to
    # `zarr_dimension_maps` might already have done this.
    group_to_dims.setdefault(group_path, {})

    # Loop over variables in this group, sorted by variable name.

    # for v in dict(sorted(group.arrays())).values():
    for v in group.variables.values():
        # Initialise mapping from the variable to its Dimension
        # objects
        var_path = v.path
        variable_to_dims[var_path] = ()

        raw_dimension_names = zarr_raw_dimension_names(v)
        if not raw_dimension_names:
            # A scalar variable has no dimensions
            continue

        # Loop over this variable's dimension names
        for name, size in zip(raw_dimension_names, v.shape):
            name_split = name.split("/")
            basename = name_split[-1]

            # --------------------------------------------------------
            # Define 'g' as the absolute path name of the group in
            # which to register the logical dimension object for this
            # dimension.
            #
            # Which group is defined will depend on the nature of the
            # dimension's 'name'.
            # --------------------------------------------------------
            if "/" not in name:
                # ----------------------------------------------------
                # Raw dimension name which contains no '/' characters
                #
                # The behaviour depends on the search algorithm
                # defined by 'group_dimension_search'.
                #
                # E.g. "dim"
                # ----------------------------------------------------
                if group_dimension_search in (
                    "closest_ancestor",
                    "furthest_ancestor",
                ):
                    # Find the names of all ancestor groups, in the
                    # appropriate order for searching.
                    group_split = group_path.split("/")
                    ancestor_names = [
                        "/".join(group_split[:n])
                        for n in range(1, len(group_split))
                    ]
                    ancestor_names[0] = "/"
                    # E.g. if the current group is /g1/g2/g3 then the
                    #      ancestor group names are [/, /g1, /g1/g2]

                    if group_dimension_search == "closest_ancestor":
                        # "closest_ancestor" searching requires the
                        # ancestor group order to be reversed,
                        # e.g. [/g1/g2, /g1, /]
                        ancestor_names = ancestor_names[::-1]

                    # Search through the ancestors in order, stopping
                    # if we find a matching dimension.
                    found_dim_in_ancestor = False
                    for g in ancestor_names:
                        zarr_dim = group_to_dims[g].get(basename)
                        if zarr_dim is not None and zarr_dim.size == size:
                            # Found a dimension in this ancestor group
                            # 'g' with the right name and size
                            found_dim_in_ancestor = True
                            break

                    if not found_dim_in_ancestor:
                        # Dimension 'basename' could not be matched to
                        # any ancestor group dimensions, so define it
                        # in the current group.
                        g = group_path

                elif group_dimension_search == "local":
                    # Assume that the dimension is different to any
                    # with same name and size defined in any ancestor
                    # group.
                    g = group_path

                else:
                    raise NetCDFError(
                        f"Bad 'zarr_dimension_search' value: "
                        f"{group_dimension_search!r}. Expected one of "
                        "'closest_ancestor', 'furthest_ancestor', 'local'"
                    )
            else:
                # ----------------------------------------------------
                # Raw dimension name contains '/' characters
                # ----------------------------------------------------
                if name.endswith("/"):
                    raise NetCDFError(
                        "Dimension names can't end with '/': "
                        f"dataset={group.dataset_name} "
                        f"variable={var_path} "
                        f"dimension_name={name}"
                    )

                g = "/".join(name_split[:-1])
                try:
                    g = group[g].path
                except KeyError:
                    raise NetCDFError(
                        f"Zarr dimension name {name!r} couldn't be found "
                        "in the group hierarchy"
                    )

            # Look for an existing Dimension
            zarr_dim = None
            if g in group_to_dims:
                # Group 'g' is already registered in the mapping
                zarr_dim = group_to_dims[g].get(basename)
                if zarr_dim is not None:
                    # Dimension 'basename' is already registered in
                    # group 'g'
                    if zarr_dim.size != size:
                        raise NetCDFError(
                            f"Zarr dimension has the wrong size: {size}. "
                            f"Expected size {zarr_dim.size} defined "
                            f"by Zarr dimension {zarr_dim.name!r} "
                            f"in group {zarr_dim.group().path!r}"
                        )
            else:
                # Initialise group 'g' in the mapping
                group_to_dims[g] = {}

            if zarr_dim is None:
                # Register a new Dimension in a group
                parent = root.get(g)
                if parent is None:
                    # Must be the root group
                    parent = root

                zarr_dim = parent._create_dimension(basename, size, False)
                group_to_dims[g][basename] = zarr_dim

            # Map the variable to the `Dimension` object
            variable_to_dims[var_path] += (zarr_dim,)

    # ----------------------------------------------------------------
    # Recursively scan all sub-groups
    # ----------------------------------------------------------------
    for g in group.groups.values():
        zarr_dimension_maps(g)


def zarr_raw_dimension_names(variable):
    """Return the raw dimension names for a variable.

    :Parameters:

        variable: `Variable`
            The variable object.

    :Returns:

        `list` of `str`
            The raw dimension names stored in the embedded
            `zarr.Variable`. A scalar variable will have an empty
            list.

    """
    metadata = variable._var.metadata
    zarr_format = metadata.zarr_format
    match zarr_format:
        case 3:
            dimensions = metadata.dimension_names
        case 2:
            dimensions = metadata.attributes.get("_ARRAY_DIMENSIONS")
        case _:
            raise NetCDFError(
                f"Can't parse a Zarr v{zarr_format} dataset. "
                "Only Zarr v3 and v2 can be parsed."
            )

    if dimensions is None:
        if variable.shape:
            raise NetCDFError(
                f"Non-scalar Zarr v{zarr_format} variable has no "
                f"dimension names: {variable.path}"
            )

        dimensions = []

    return dimensions


def zarr_read(dataset, options):
    """Read a dataset with `zarr`.

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
            Additional keyword parameters to pass to `zarr.open`.

    :Returns:

        (`zarr.Group`, `dict`, library)
            The opened dataset, the dataset's global attributes, and
            the `zarr` library itself.

    """
    import zarr

    dataset_name = ""
    protocol = -1

    if isinstance(dataset, zarr.Group):
        nc = dataset
        library = get_library(dataset)
        dataset_name = zarr_get_dataset_name(dataset)
        owns_accessor = False

        if not dataset_name:
            dataset_name = "<zarr-like>"
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
            raise ValueError(f"Can't set mode={mode!r} in zarr_options")

        dataset, dataset_name, protocol = get_dataset_name_and_protocol(
            dataset
        )
        nc = zarr.open(dataset, mode="r", **options)

        library = zarr
        owns_accessor = True

    return {
        "dataset_name": dataset_name,
        "protocol": protocol,
        "nc": nc,
        "attrs": nc.attrs,
        "backend_api": "zarr",
        "library": library,
        "owns_accessor": owns_accessor,
    }


def zarr_parse_group_structure(group):
    """Parse the group structure for the `zarr` backend.

    Parses variables, dimensions, and sub-groups, recursively.

    :Parameters:

        group: `Group` or `Dataset`
            The group to be parsed.

    :Returns:

        `None`

    """
    # Create variables in this group
    for name, var in sorted(dict(group._grp.arrays()).items()):
        group._create_variable(name, var, var.attrs, var.shape)

    # Create subgroups
    for name, grp in sorted(dict(group._grp.groups()).items()):
        group._create_group(name, grp, grp.attrs)

    # Starting from the root group, i) create dimensions in all
    # groups, and ii) attach dimensions to each variable.
    if group.is_root:
        root = group
        root._group_to_dims = {}
        root._variable_to_dims = {}

        # Populate root._group_to_dims and root._variable_to_dims
        zarr_dimension_maps(root)

        for path, dims in sorted(root._group_to_dims.items()):
            group = root[path]
            for name, dim in sorted(dims.items()):
                group._dimensions[name] = dim

            # Set each variable's `_dim` attribute. This is important,
            # as it allows `Variable.get_dims` to work.
            for name, var in group.variables.items():
                var._dims = root._variable_to_dims[var.path]

        del root._group_to_dims, root._variable_to_dims
