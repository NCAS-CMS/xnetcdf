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

    The dataset is opened with `xarray.open_datatree` option
    ``decode_cf=False``.

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
            `xarray.open_datatree`. The keyword argument
            ``decode_cf=False`` is always automatially applied, even
            when not provided in *options*, and can't be set to
            different values.

    :Returns:

        (`xarray.DataTree`, `dict`, library)
            The opened dataset, the dataset's global attributes, and
            the `xarray` library itself.

    """
    import xarray

    dataset_name = None
    protocol = -1

    undecode_cf = True

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
        decode_cf = options.pop("decode_cf", False)
        if decode_cf:
            raise ValueError("Can't set decode_cf=True in xarray_options")

        if "chunks" not in options:
            options["chunks"] = "auto"

        dataset, dataset_name, protocol = get_dataset_name_and_protocol(
            dataset
        )
        nc = xarray.open_datatree(dataset, decode_cf=False, **options)

        library = xarray
        owns_accessor = True

        # No need to reverse any xarray CF encoding because
        # decode_cf=False
        undecode_cf = False

    if undecode_cf:
        # Reverse any xarray-specific CF decoding
        nc = xarray_undecode_cf(nc)

    return {
        "dataset_name": dataset_name,
        "protocol": protocol,
        "nc": nc,
        "attrs": nc.attrs,
        "backend_api": "xarray",
        "library": library,
        "owns_accessor": owns_accessor,
    }



_CF_ENCODING_KEYS = frozenset({"_FillValue", "missing_value"})


def _undecode_cf_dataset(ds):
    """Reverse `xarray.decode_cf` on a single `xarray.Dataset`.

    .. versionadded:: 0.3.0

    :Parameters:

        ds: `xarray.Dataset`
            The dataset to undecode.

    :Returns:

        `xarray.Dataset`
            The undecoded dataset.

    """
    import xarray
    from xarray.coding.strings import check_vlen_dtype
    from xarray.conventions import (
        _update_bounds_encoding,
        encode_cf_variable,
    )

    attrs = dict(ds.attrs)
    coordinates = ds.encoding.get("coordinates")
    if coordinates is not None:
        attrs.setdefault("coordinates", coordinates)

    # Shallow-copy variables and their encodings directly (avoiding
    # Dataset.__init__, which strips 'encoding' from IndexVariables)
    variables = {}
    for key, v in ds.variables.items():
        var = v.copy(deep=False)
        var.attrs = dict(var.attrs)
        var.encoding = dict(var.encoding)

        # Restore the coordinates attribute only if it actually
        # existed in 'encoding'
        if "coordinates" in var.encoding:
            coords_attr = var.encoding.pop("coordinates")
            if coords_attr is not None:
                var.attrs.setdefault("coordinates", coords_attr)

        # Prevent CFMaskCoder from inventing _FillValue=nan on float
        # variables that did not originally have a _FillValue on disk
        if "_FillValue" not in var.attrs:
            var.encoding.setdefault("_FillValue", None)

        variables[key] = var

    orig_attrs = {key: dict(v.attrs) for key, v in ds.variables.items()}

    # Reverse CF variable decoding only where CF encoding metadata or
    # decoded time/cftime dtypes exist (leaving strings as strings and
    # keeping decode_cf=False inputs lazy)
    _update_bounds_encoding(variables)
    for key, var in list(variables.items()):
        is_string = var.dtype.kind in {"U", "S", "T"} or (
            var.dtype.kind == "O"
            and check_vlen_dtype(var.dtype) in {str, bytes}
        )
        if is_string:
            continue

        has_cf_encoding = any(
            var.encoding.get(k) is not None for k in _CF_ENCODING_KEYS
        )
        if var.dtype.kind in {"M", "m", "O"} or has_cf_encoding:
            variables[key] = encode_cf_variable(var, name=key)

    # Restore explicitly supplied bounds attributes that encoding
    # strips during serialization cleanup (e.g. matching 'units' on
    # bounds variables)
    for var in variables.values():
        bounds = var.attrs.get("bounds")
        if isinstance(bounds, str):
            bnds_name = bounds.rsplit("/", 1)[-1]
            if bnds_name in variables:
                for attr, val in orig_attrs.get(bnds_name, {}).items():
                    variables[bnds_name].attrs.setdefault(attr, val)

    # Only 1-d dimension-matching variables live in "coords"
    dim_coords = {key: v for key, v in variables.items() if v.dims == (key,)}
    data_vars = {key: v for key, v in variables.items() if v.dims != (key,)}

    # Create the undecoded dataset
    out = xarray.Dataset(data_vars=data_vars, coords=dim_coords, attrs=attrs)

    # Preserve dataset and group encodings (including
    # 'unlimited_dims')
    out.encoding = {
        key: set(v) if isinstance(v, set) else v
        for key, v in ds.encoding.items()
        if key != "coordinates"
    }
    return out

def xarray_undecode_cf(ds):
    """Reverse any effects of `xarray.decode_cf`.

    .. versionadded:: 0.3.0

    .. warning :: If the dataset was opened from disk, then for
                  optimal performance and minimal memory usage it
                  should have been opened with ``decode_cf=False`` or
                  be backed by Dask chunks, neither of which is the
                  default in `xarray.open_dataset` or
                  `xarray.open_datatree`. If the input was opened from
                  disk using ``decode_cf=True`` and without Dask
                  chunks, then the automatic reversal of xarray's CF
                  decoding on selected variables (i.e. those with
                  ``_FillValue`` or ``missing_value`` attributes; or
                  those decoded into non-numeric time or timedelta
                  objects) will eagerly load those data arrays into
                  memory.
    
    :Parameters:

        ds: `xarray.Dataset` or `xarray.DataTree`
            The dataset to undecode.

    :Returns:

        `xarray.Dataset` or `xarray.DataTree`
            The undecoded dataset.

    """
    import xarray

    if isinstance(ds, xarray.Dataset):
        return _undecode_cf_dataset(ds)

    if isinstance(ds, xarray.DataTree):
        nodes = {
            path: _undecode_cf_dataset(node.to_dataset(inherit=False))
            for path, node in ds.subtree_with_keys
        }
        return xarray.DataTree.from_dict(nodes, name=ds.name)

    raise TypeError(
        f"Expected xarray.Dataset or xarray.DataTree. Got: {type(ds)!r}"
    )


def _undecode_cf_dataset_old(ds):
    """Reverse xarray.decode_cf on a single `xarray.Dataset`.

    .. versionadded:: 0.3.0

    :Parameters:

        ds: `xarray.Dataset`
            The dataset to undecode.

    :Returns:

        `xarray.Dataset`
            The undecoded dataset.

    """
    import xarray

    attrs = dict(ds.attrs)
    coordinates = ds.encoding.get("coordinates")
    if coordinates is not None:
        attrs.setdefault("coordinates", coordinates)

    # Shallow-copy variables and their encodings directly (avoiding
    # Dataset.__init__, which strips 'encoding' from IndexVariables)
    variables = {}
    for k, v in ds.variables.items():
        var = v.copy(deep=False)
        var.attrs = dict(var.attrs)
        var.encoding = dict(var.encoding)

        # Restore the coordinates attribute only if it actually
        # existed in 'encoding'
        if "coordinates" in var.encoding:
            coords_attr = var.encoding.pop("coordinates")
            if coords_attr is not None:
                var.attrs.setdefault("coordinates", coords_attr)

        # Prevent CFMaskCoder from inventing _FillValue=nan on float
        # variables that did not originally have a _FillValue on disk
        if "_FillValue" not in var.attrs:
            var.encoding.setdefault("_FillValue", None)

        variables[k] = var

    orig_attrs = {key: dict(v.attrs) for key, v in ds.variables.items()}

    # Reverse CF variable decoding (times, scale/offset, _FillValue,
    # char arrays)
    variables, attrs = xarray.conventions.cf_encoder(variables, attrs)

    # Restore explicitly supplied bounds attributes that cf_encoder
    # strips during serialization cleanup (e.g. matching 'units' on
    # bounds variables)
    for var in variables.values():
        bounds = var.attrs.get("bounds")
        if isinstance(bounds, str):
            bnds_name = bounds.rsplit("/", 1)[-1]
            if bnds_name in variables:
                for attr, val in orig_attrs.get(bnds_name, {}).items():
                    variables[bnds_name].attrs.setdefault(attr, val)

    # Only 1-d dimension-matching variables live in "coords"
    dim_coords = {key: v for key, v in variables.items() if v.dims == (key,)}
    data_vars = {key: v for key, v in variables.items() if v.dims != (key,)}

    # Create the undecoded dataset
    out = xarray.Dataset(data_vars=data_vars, coords=dim_coords, attrs=attrs)

    # Preserve datase and group encodings (including 'unlimited_dims')
    out.encoding = {
        key: set(v) if isinstance(v, set) else v
        for key, v in ds.encoding.items()
        if key != "coordinates"
    }
    return out


def xarray_undecode_cf_old(ds):
    """Reverse any effects of `xarray.decode_cf`.

    .. versionadded:: 0.3.0

    :Parameters:

        ds: `xarray.Dataset` or `xarray.DataTree`
            The dataset to undecode.

    :Returns:

        `xarray.Dataset` or `xarray.DataTree`
            The undecoded dataset.

    """
    import xarray

    if isinstance(ds, xarray.Dataset):
        return _undecode_cf_dataset(ds)

    if isinstance(ds, xarray.DataTree):        
        nodes = {
            path: _undecode_cf_dataset(node.to_dataset(inherit=False))
            for path, node in ds.subtree_with_keys
        }
        return xarray.DataTree.from_dict(nodes, name=ds.name)
        
    raise TypeError(
        f"Expected xarray.Dataset or xarray.DataTree. Got: {type(ds)!r}"
    )
