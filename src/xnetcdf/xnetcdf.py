from collections.abc import Mapping
from itertools import chain
from math import prod

import numpy as np

from .utils import (
    NetCDFError,
    cdl_format,
    get_dimensions_from_defining_group,
    h5py_read,
    hdf5_dimension_names,
    hdf5_parse_group_structure,
    netCDF4_parse_group_structure,
    netCDF4_read,
    netcdf_file_close,
    netcdf_file_dtype,
    netcdf_file_parse_group_structure,
    netcdf_file_read,
    parse_attributes,
    ppfive_read,
    pyfive_read,
    xarray_parse_group_structure,
    xarray_read,
    zarr_parse_group_structure,
    zarr_read,
)

# Map backend names to dataset-read functions. This ordered dictionary
# defines the default order of functions attempted to read the
# dataset.
#
# Note to developers: If you change the order of this dictionary, or
#                     add a new key/value pair, you must update the
#                     `Dataset` docstring.
_read_functions = {
    "pyfive": pyfive_read,
    "zarr": zarr_read,
    "ppfive": ppfive_read,
    "netCDF4": netCDF4_read,
    "netcdf_file": netcdf_file_read,
    "h5py": h5py_read,
    "xarray": xarray_read,
}
backends = tuple(_read_functions)

# np.printoptions parameters for `dump` method output (17 significant
# digits is enough to fully represent every possible bit of precision
# for 64-bit floats).
_printoptions = {"precision": 17, "floatmode": "maxprec"}


class Mixin:
    """Mixin class for methods common to all classes.

    Mixin class for methods common `Dimension`, `Variable`, and
    `Group`.

    """

    __hash__ = None

    # Quantum of indentation for the `dump` method
    __indent = "    "

    @property
    def backend_api(self):
        """The name of the backend API.

        The backend API identifies the nature of interface of the
        backend library to the dataset. In general, the name of the
        backend API is the same as the name of underlying backend
        library that provides access the dataset, however these might
        be different if the dataset was defined as (a registered)
        subclass of the one of the allowed backends.

        .. seealso:: `backend_library`, `dataset`

        :Returns:

            `str`
                The name of the backend API, one of ``'pyfive'``,
                ``'zarr'``, ``'ppfive'``, ``'netCDF4'``,
                ``'netcdf_file'``, ``'h5py'``, and ``'xarray'``.

        """
        return self.root._backend_api

    @property
    def backend_library(self):
        """The backend library.

        The backend library provides the backend object that accesses
        the dataset.

        .. seealso:: `backend_api`, `dataset`

        :Returns:

                The library that provides the backend.

        """
        return self.root._backend_library

    @property
    def dataset(self):
        """The dataset definition, as originally passed to `Dataset`.

        If an original string-like dataset definition contained tilde
        or environment variables, then these are expanded in the
        returned string.

        .. seealso:: `filename`, `dataset_name`, `is_local`,
                     `protocol`, `backend_library`, `backend_api`

        :Returns:

                The dataset definition. May be anything acceped by the
                *dataset* parameter of `xnetcdf.Dataset`.

        """
        return self.root._dataset

    @property
    def dataset_name(self):
        """The name of the dataset.

        This is an alias for `filename`.

        .. seealso:: `dataset`, `is_local`, `protocol`, `dataset`

        :Returns:

            `str`
                The name of the dataset. If the dataset name is not
                known then an empty string is returned.

        """
        return self.root._dataset_name

    @property
    def filename(self):
        """The name of the dataset.

        This is an alias for `dataset_name`.

        .. seealso:: `dataset_name`

        :Returns:

            `str`
                The name of the dataset. If the dataset name is not
                known then an empty string is returned.

        """
        return self.dataset_name

    @property
    def is_local(self):
        """Whether the dataset is on the local file system.

        It is usually possible to ascertain whether the dataset is on
        the local file system from the dataset definition (as returned
        by `dataset`), but in those cases when it is not possible,
        `is_local` will return `None`, and `protocol` will raise an
        `AttributeError`.

        .. seealso:: `dataset`, `dataset_name`, `protocol`

        :Returns:

            `bool` or `None`
                `True` if the dataset is on the local file system
                (i.e. `protocol` returns ``'file'``), and `False` if
                the dataset is on a remote file system. If the file
                system is unknown then `None` will be returned.

        """
        return self.root._is_local

    @property
    def parent(self):
        """The parent group.

        .. seealso:: `root`

        :Returns:

            `Group` or `Dataset` or `None`
                The parent group, or `None` if there is no parent
                group.

        """
        return self._parent

    @property
    def protocol(self):
        """The file system protocol for the dataset.

        It is usually possible to ascertain the file system protocol
        from the dataset definition (as returned by `dataset`), but in
        those cases when it is not possible, `protocol` will raise an
        `AttributeError` and `is_local` will return `None`.

        .. seealso:: `dataset`, `dataset_name`, `is_local`

        :Returns:

            `str` or `None`
                The file system protocol. The local file system is
                indicated by ``'file'``. If the file system protocol
                is unknown then an `AttributeError` will be raised.

        """
        try:
            return self.root._protocol
        except AttributeError:
            raise AttributeError("Can't determine the file system protocol")

    @property
    def root(self):
        """The root group.

        .. seealso:: `parent`

        :Returns:

            `Dataset`
                The root group.

        """
        root = getattr(self, "_root", None)
        if root is None:
            return self.parent.root

        return root


class Mixin2:
    """Mixin class for methods common `Variable` and `Group`."""

    @property
    def attrs(self):
        """The attributes.

        .. seealso:: `ncattrs`, `getncattr`

        :Returns:

            `dict`
                The attribute values, keyed by their names.

        """
        return self._attrs

    def getncattr(self, name):
        """Get an attribute value by name.

        .. seealso:: `attrs`, `ncattrs`

        :Parameters:

            name: `str`
                The attribute name.

        :Returns:

                The attribute value. An `AttributeError` is raised if
                the attribute does not exist.

        """
        try:
            return self.attrs[name]
        except KeyError:
            raise AttributeError(
                f"{self.__class__.__name__!r} object has no attribute "
                f"{name!r}"
            )

    def ncattrs(self):
        """Return a list of attribute names.

        .. seealso:: `attrs`, `getncattr`

        :Returns:

            `list` of `str`
                The attribute names.

        """
        return list(self.attrs)


class Dimension(Mixin):
    """A netCDF dimension.

    :Parameters:

        name: `str`
            The name of the dimension in its parent group.

        size: `int`
            The size of the dimension.

        isunlimited: `bool`
            True if the dimension is unlimited.

        parent: `Group` or `Dataset`
            The group in which this dimension is defined.

    """

    def __init__(self, name, size, isunlimited, parent):
        self._name = name
        self._size = size
        self._isunlimited = isunlimited
        self._parent = parent

    def __len__(self):
        """The size of the dimension."""
        return self.size

    def __repr__(self):
        unlimited = ", unlimited" if self.isunlimited() else ""
        return (
            f"{self.name}: <{__package__}.{self.__class__.__name__}: "
            f"{self.path}, size={self.size}{unlimited}>"
        )

    @property
    def name(self):
        """The name of the dimension in its parent group.

        .. seealso:: `path`

        :Returns:

            `str`
                The relative name (e.g. ``'time'``).

        """
        return self._name

    @property
    def path(self):
        """The absolute path of the dimension.

        .. seealso:: `name`

        :Returns:

            `str`
                The absolute path of the dimension, e.g. ``'/lat'`` or
                ``'/group/time'``.

        """
        path = getattr(self, "_path", None)
        if path is None:
            parent = self.parent
            if parent.is_root:
                path = f"/{self.name}"
            else:
                path = f"{parent.path}/{self.name}"

            self._path = path

        return path

    @property
    def size(self):
        """The size of the dimension.

        .. seealso:: `isunlimited`

        :Returns:

            `int`
                The size.

        """
        return self._size

    def dump(
        self,
        display=True,
        _prefix=None,
        _level=0,
        _structure=False,
    ):
        """A full description of the dimension.

        .. seealso:: `structure`

        :Parameters:

            display: `bool`, optional
                If False then return the description as a string. By
                default the description is printed.

        :Returns:

            `None` or `str`
                The description. If *display* is True then the
                description is printed and `None` is
                returned. Otherwise the description is returned as a
                string.

        """
        indent = self._Mixin__indent
        i0 = indent * _level

        # _prefix is not currently used
        _prefix = ""

        lines = [f"{i0}{_prefix}{self!r}"]

        out = "\n".join(lines)
        if not display:
            return out

        print(out)

    def group(self):
        """The parent group that defines this dimension.

        This is an alias for `parent`.

        .. seealso:: `parent`, `root`

        :Returns:

            `Group` or `Dataset`
                The parent group.

        """
        return self.parent

    def isunlimited(self):
        """Whether the dimension is unlimited.

        .. seealso:: `size`

        :Returns:

            `bool`
                `True` if the dimension is unlimited, `False`
                otherwise.

        """
        return self._isunlimited

    def structure(
        self,
        display=True,
        _prefix=None,
        _level=0,
    ):
        """A purely structural description of the dimension.

        This is identical to `dump`.

        .. seealso:: `dump`

        :Parameters:

            display: `bool`, optional
                If False then return the description as a string. By
                default the description is printed.

        :Returns:

            `None` or `str`
                The description. If *display* is True then the
                description is printed and `None` is
                returned. Otherwise the description is returned as a
                string.

        """
        return self.dump(
            display=display,
            _prefix=_prefix,
            _level=_level,
            _structure=True,
        )


class Variable(Mixin, Mixin2):
    """A netCDF variable.

    :Data access and indexing:

    The data array of an `Variable` instance is accessed by direct
    indexing, following whatever indexing rules are allowed by the
    underlying backend object.

    The requested subspace is always returned as a `numpy` array.

    .. note:: Since the interpretation of the indices is handled
              entirely by the underlying backend object, the same
              indices may define a different subspace for different
              underlying backends.

    :Attributes:

    Attributes are derived from the underlying backend object, and not
    directly from the dataset on disk. An attribute that exists in a
    dataset on disk but has been hidden by the underlying backend
    object will not be available to `xnetcdf`. For instance, a backend
    that follows the CF conventions might remove ``coordinates`` and
    ``bounds`` attributes.

    Attributes that have special structural meanings according to the
    netCDF-4 conventions will not appear in the attribute collection.
    These attributes are ``CLASS``, ``NAME``, ``REFERENCE_LIST``,
    ``DIMENSION_LIST``, ``DIMENSION_LABELS``, and
    ``_ARRAY_DIMENSIONS``, as well as any attributes that start with
    ``_Netcdf4``, ``_nc``, or ``_NC``.

    :Parameters:

        name: `str`
            The name of the variable in its parent group.

        parent: `Group` or `Dataset`
            The parent group in which this variable is defined.

        var:
            The underlying backend variable object provided by the
            backend library. This is available with the
            `backend_accessor` attribute.

        var_attrs: `dict`
            The raw attributes of *var*.

        shape: `None` or `tuple` of `int`, optional
            The shape of the variable's data array. If `None` (the
            default) then the shape is retrieved later from *var*, if
            required.

    """

    def __init__(self, name, parent, var, var_attrs, shape=None):
        self._name = name
        self._var = var
        self._parent = parent
        self._var_attrs = var_attrs
        self._attrs = parse_attributes(self, var_attrs)
        if shape is not None:
            self._shape = shape

    def __getitem__(self, indices):
        """Return a subspace of the data array defined by indices."""
        array = self._var[indices]
        match self.backend_api:
            case "netcdf_file":
                # Need to copy the numpy array returned by
                # scipy.io.netcdf_file with mmap=True. See the
                # comments in `netcdf_file_close` for details.
                array = array.copy()
            case "xarray":
                # Get the numpy array from the Dask array
                array = array.values

        if not isinstance(array, np.ndarray):
            array = np.array(array)

        return array

    def __len__(self):
        """The size of leading data array dimension."""
        shape = self.shape
        if shape:
            return shape[0]

        raise TypeError("len() of unsized object (scalar variable)")

    def __repr__(self):
        # Resolve the dimension objects to get their full paths
        try:
            dim_paths = [d.path for d in self.get_dims()]
            if len(dim_paths) == 1:
                dims = f"({dim_paths[0]},)"
            else:
                dims = f"({', '.join(dim_paths)})"
        except Exception:
            # Fallback if resolution fails for any reason
            dims = self.dimensions

        return (
            f"{self.name}: <{__package__}.{self.__class__.__name__}: "
            f"{self.path}, shape={self.shape}, dimensions={dims}>"
        )

    @property
    def __orthogonal_indexing__(self):
        """Flag to indicate whether indexing is orthogonal."""
        orthogonal_indexing = getattr(self, "_orthogonal_indexing", None)
        if orthogonal_indexing is None:
            orthogonal_indexing = getattr(
                self._var, "__orthogonal_indexing__", False
            )
            self._orthogonal_indexing = orthogonal_indexing

        return orthogonal_indexing

    @property
    def backend_accessor(self):
        """The backend object that accesses the variable.

        The backend accessor is the interface to the dataset.

        .. seealso:: `backend_library`, `dataset`

        :Returns:

                The backend object.

        """
        return self._var

    @property
    def chunks(self):
        """The data array chunk shape.

        .. seealso:: `shards`, `chunking`

        :Returns:

            `None` or `tuple` of `int`
                The chunk shape, e.g. ``(5, 6, 7)``. If the data is
                contiguous then `None` is returned.

        """
        chunks = getattr(self, "_chunks", None)
        if chunks is None:
            match self.backend_api:
                case "pyfive" | "h5py" | "ppfive":
                    chunks = self._var.chunks

                case "netCDF4":
                    chunks = self._var.chunking()
                    if chunks == "contiguous":
                        chunks = None
                    elif chunks is not None:
                        chunks = tuple(chunks)

                case "netcdf_file":
                    chunks = None

                case "zarr":
                    chunks = self._var.chunks
                    if not chunks:
                        chunks = None

                case "xarray":
                    chunks = self._var.encoding.get("chunksizes")

                case _:
                    raise NotImplementedError(
                        "Need to implement 'chunks' for backend API "
                        f"{self.backend_api!r}"
                    )

            self._chunks = chunks

        return chunks

    @property
    def dimension_paths(self):
        """The variable dimension absolute paths.

        .. seealso:: `dimensions`, `get_dims`

        :Returns:

            `tuple`
                The dimension absolute paths (i.e. start with ``/``),
                in the order of the data array dimensions.

        """
        paths = getattr(self, "_dimension_paths", None)
        if paths is None:
            paths = tuple(dim.path for dim in self.get_dims())
            self._dimension_paths = paths

        return paths

    @property
    def dimensions(self):
        """The variable dimension relative names.

        .. seealso:: `dimension_paths`, `get_dims`

        :Returns:

            `tuple`
                The dimension names, relative to their defining group,
                in the order of the data array dimensions.

        """
        dimensions = getattr(self, "_dimensions", None)
        if dimensions is None:
            dimensions = tuple(dim.name for dim in self.get_dims())
            self._dimensions = dimensions

        return dimensions

    @property
    def dtype(self):
        """The numpy data type of the variable."""
        dtype = getattr(self, "_dtype", None)
        if dtype is None:
            match self.backend_api:
                case (
                    "pyfive"
                    | "zarr"
                    | "netCDF4"
                    | "h5py"
                    | "xarray"
                    | "ppfive"
                ):
                    dtype = self._var.dtype

                case "netcdf_file":
                    dtype = netcdf_file_dtype(self)

                case _:
                    raise NotImplementedError(
                        "Need to implement 'dtype' for backend API"
                        f"{self.backend_api!r}"
                    )

            if dtype is not str and dtype != np.dtypes.StringDType():
                dtype = np.dtype(f"{dtype.kind}{dtype.itemsize}")

            self._dtype = dtype

        return dtype

    @property
    def maxshape(self):
        """The maximum dimension lengths of the variable.

        .. seealso:: `shape`

        :Returns:

            `tuple`
                The maximum dimension lengths (e.g. ``(180,
                360)``). Unlimited dimensions are represented by
                `None` (e.g. ``(None, 96, 73)``)

        """
        maxshape = getattr(self, "_maxshape", None)
        if maxshape is None:
            maxshape = tuple(
                None if dim.isunlimited() else dim.size
                for dim in self.get_dims()
            )
            self._maxshape = maxshape

        return maxshape

    @property
    def name(self):
        """The name of the variable in its parent group.

        .. seealso:: `path`

        :Returns:

            `str`
                The relative name (e.g. ``'latitude'``).

        """
        return self._name

    @property
    def ndim(self):
        """The number of dimensions for the variable.

        .. seealso:: `size`, `shape`

        :Returns:

            `int`
                The number of dimensions.

        """
        ndim = getattr(self, "_ndim", None)
        if ndim is None:
            ndim = len(self.shape)
            self._ndim = ndim

        return ndim

    @property
    def path(self):
        """The absolute path of the variable.

        .. seealso:: `name`

        :Returns:

            `str`
                The absolute path of the variable, e.g. ``'/time'`` or
                ``'/group/latitude'``.

        """
        path = getattr(self, "_path", None)
        if path is None:
            parent = self.parent
            if parent.is_root:
                path = f"/{self.name}"
            else:
                path = f"{parent.path}/{self.name}"

            self._path = path

        return path

    @property
    def shape(self):
        """The dimension lengths of the variable.

        .. seealso:: `ndim`, `size`, `maxshape`

        :Returns:

            `tuple` of `int`
                The dimension lengths, e.g. ``(12, 96, 73)``.

        """
        shape = getattr(self, "_shape", None)
        if shape is None:
            shape = self._var.shape
            self._shape = shape

        return shape

    @property
    def shards(self):
        """The data shard shape.

        .. seealso:: `chunks`, `chunking`

        :Returns:

            `None` or `tuple` of `int`
                The shard shape (e.g. ``(12, 96, 73)``) for a sharded
                Zarr variable, or `None` for a non-sharded Zarr
                variable or a variable in a non-Zarr dataset.

        """
        if hasattr(self, "_shards"):
            return self._shards

        match self.backend_api:
            case "zarr":
                shards = self._var.shards
            case _:
                shards = None

        self._shards = shards
        return shards

    @property
    def size(self):
        """The total number of elements in the variable's data.

        .. seealso:: `ndim`, `shape`

        :Returns:

            `int`
                The number of elements.

        """
        size = getattr(self, "_size", None)
        if size is None:
            size = prod(self.shape)
            self._size = size

        return size

    def chunking(self):
        """The data array chunk shape.

        .. seealso:: `chunks`, `shards`

        :Returns:

            `list` or ``'contiguous'`` or `None`
                The chunk shape, e.g. ``[5, 6, 7]``. For contiguous
                data in a dataset that does support chunking,
                ``'contiguous'`` is returned. If the dataset doesn't
                support chunking (such as netCDF-3) then `None` is
                returned.

        """
        chunking = getattr(self, "_chunking", None)
        if chunking is None:
            chunks = self.chunks
            match self.backend_api:
                case "pyfive" | "zarr" | "xarray" | "h5py" | "ppfive":
                    if chunks is None:
                        chunking = "contiguous"
                    else:
                        chunking = list(chunks)

                case "netCDF4":
                    if chunks is None:
                        if self.root._grp.data_model.startswith("NETCDF3"):
                            chunking = None
                        else:
                            chunking = "contiguous"
                    else:
                        chunking = list(chunks)

                case "netcdf_file":
                    chunking = None

                case _:
                    raise NotImplementedError(
                        "Need to implement 'chunking' for backend API"
                        f"{self.backend_api!r}"
                    )

            self._chunking = chunking

        return chunking

    def dump(
        self,
        display=True,
        data=False,
        _prefix=None,
        _level=0,
        _structure=False,
    ):
        """A full description of the variable.

        .. seealso:: `structure`

        :Parameters:

            display: `bool`, optional
                If False then return the description as a string. By
                default the description is printed.

            data: `bool`, optional
                If True then include a summary of the variable's data
                array. If False (the default) then don't include a
                data summary.

        :Returns:

            `None` or `str`
                The description. If *display* is True then the
                description is printed and `None` is
                returned. Otherwise the description is returned as a
                string.

        """
        indent = self._Mixin__indent
        i0 = indent * _level
        i1 = indent * (_level + 1)
        i2 = indent * (_level + 2)

        # _prefix is not currently used
        _prefix = ""

        lines = [f"{i0}{_prefix}{self!r}"]

        if _structure:
            data = False

        printoptions = _printoptions
        if data and "linewidth" not in printoptions:
            # Set the np.printoptions linewidth
            printoptions = printoptions | {"linewidth": len(lines[0])}

        with np.printoptions(**printoptions):
            # Attributes
            if not _structure and self.attrs:
                lines.append(f"{i1}Attributes:")
                lines.extend(
                    f"{i2}{name}: {value!r}"
                    for name, value in self.attrs.items()
                )

            if data:
                lines.append(f"{i1}Data {self.dtype.name}:")
                data_string = np.array2string(
                    self[...], separator=", ", prefix=i2
                )
                lines.append(f"{i2}{data_string}")

        out = "\n".join(lines)
        if not display:
            return out

        print(out)

    def get_dims(self):
        """Return the dimensions of the variable.

        .. seealso:: `dimensions`

        :Returns:

            `tuple` of `Dimension`
                The dimensions for the variable.

        """
        # Note: This method is not called in `__init__`, because for
        #       some backend APIs (e.g. `zarr`) the `Dimension`
        #       objects are only available after the entire group and
        #       variable structure has been parsed.
        dims = getattr(self, "_dims", None)
        if dims is None:
            match self.backend_api:
                case "pyfive" | "h5py" | "ppfive":
                    dims = get_dimensions_from_defining_group(
                        self, hdf5_dimension_names(self)
                    )

                case "netCDF4":
                    root = self.root
                    dims = [
                        root[ndim.group().path].dimensions[ndim.name]
                        for ndim in self._var.get_dims()
                    ]

                case "netcdf_file":
                    dimensions = self.root.dimensions
                    dims = [dimensions[dim] for dim in self._var.dimensions]

                case "xarray":
                    dims = get_dimensions_from_defining_group(
                        self, self._var.dims
                    )

                case "zarr":
                    raise RuntimeError(
                        "You shouldn't be here: self._dims should have "
                        "already been set to something other than None by "
                        "the zarr_parse_group_structure function"
                    )

                case _:
                    raise NotImplementedError(
                        "Need to implement 'get_dims' for backend API"
                        f"{self.backend_api!r}"
                    )

            dims = tuple(dims)
            self._dims = dims

        return dims

    def getValue(self):
        """Return the data value of a scalar variable.

        :Returns:

        The scalar value.

        """
        if self.shape:
            raise IndexError(
                "to retrieve values from a non-scalar variable, use slicing"
            )

        return self[()]

    def group(self):
        """The parent group that defines this variable.

        This is an alias for `parent`.

        .. seealso:: `parent`, `root`

        :Returns:

            `Group` or `Dataset`
                The parent group.

        """
        return self.parent

    def structure(
        self,
        display=True,
        _prefix=None,
        _level=0,
    ):
        """A purely structural description of the variable.

        This similar to `dump`, but no attributes and no data are
        shown.

        .. seealso:: `dump`

        :Parameters:

            display: `bool`, optional
                If False then return the description as a string. By
                default the description is printed.

        :Returns:

            `None` or `str`
                The description. If *display* is True then the
                description is printed and `None` is
                returned. Otherwise the description is returned as a
                string.

        """
        return self.dump(
            display=display,
            _prefix=_prefix,
            _level=_level,
            _structure=True,
        )


class Group(Mixin, Mixin2, Mapping):
    """A netCDF group.

    :Indexing:

    A group or variable object, anywhere in the group hierarchy, can
    be accessed by indexing an `Group` instance with the object's
    name.

    Keys can be provided as an absolute path name or as a path name
    that is relative to the root group. Relative path names may
    include ``.`` and ``..`` elements to indicate positions in the
    group hierarchy. Consecutive ``/`` characters are reduced to a
    single ``/``, and a trailing ``/`` character is always allowed.

    * If the key maps to a group, the `Group` instance is returned.

    * If the key maps to a variable, the `Variable` instance is
      returned.

    :Attributes:

    Attributes are derived from the underlying backend object, and not
    directly from the dataset on disk. An attribute that exists in a
    dataset on disk but has been hidden by the underlying backend
    object will not be available to `xnetcdf`. For instance, a backend
    that follows the CF conventions might remove ``coordinates`` and
    ``bounds`` attributes.

    Attributes that have special structural meanings according to the
    netCDF-4 conventions will not appear in the attribute collection.
    These attributes are ``CLASS``, ``NAME``, ``REFERENCE_LIST``,
    ``DIMENSION_LIST``, ``DIMENSION_LABELS``, and
    ``_ARRAY_DIMENSIONS``, as well as any attributes that start with
    ``_Netcdf4``, ``_nc``, or ``_NC``.

    :Parameters:

        name: `str`
            The name of the group in its parent group. The root group
            has the name ``''``.

        parent: `Group` or `None`
            The parent group. Set to `None` if there is no parent
            (i.e. the group is the root group).

        root: `Dataset`
            The root group.

        grp:
            The underlying backend group object provided by the
            backend library. This is available with the
            `backend_accessor` attribute.

        grp_attrs: `dict`
            The raw attributes of *grp*.

    """

    # Store references to classes for creating dimensions, variables
    # and sub-groups in `_create_dimension`, `_create_variable` and
    # `_create_group` respectively.
    #
    # Note: __Group will be re-set to `Group` after the `Group` class
    #       has finished defining itself.
    __Dimension = Dimension
    __Variable = Variable
    __Group = None

    def __init__(self, name, parent, root, grp, grp_attrs):
        self._name = name
        self._parent = parent
        self._root = root
        self._grp = grp
        self._is_root = parent is None

        self._attrs = parse_attributes(self, grp_attrs)

        self._dimensions = {}
        self._variables = {}
        self._groups = {}
        self._parse_group_structure()

    def __getitem__(self, path):
        """Get a variable or group from its path.

        Keys can be provided as an absolute path name or as a path
        name that is relative to the root group. Relative path names
        may include ``.`` and ``..`` elements to indicate positions in
        the group hierarchy. Consecutive ``/`` characters are reduced
        to a single ``/``, and a trailing ``/`` character is always
        allowed.

        """
        if path == "":
            return self

        # Still here? Determine the starting point
        current = self
        if path.startswith("/"):
            current = self.root
        else:
            current = self

        # Split the path into parts (ignoring empty strings from
        # double-slashes)
        segments = [s for s in path.split("/") if s]

        # Handle a path of "/", "//", "///", etc.
        if not segments:
            return current

        # Still here? Then loop through the segments
        for i, part in enumerate(segments):
            if part == "..":
                if current.is_root:
                    if path.startswith("/"):
                        start = ""
                    else:
                        start = f" from group {self.path}"

                    raise KeyError(
                        f"Invalid path {path!r}{start}: Attempted to "
                        "navigate above the root group."
                    )

                # Move up one group
                current = current.parent
                continue

            if part == ".":
                continue

            # Group/Variable navigation
            if part in current.groups:
                current = current.groups[part]
            elif part in current.variables:
                # A variable must be the final element in a path
                if i == len(segments) - 1:
                    return current.variables[part]

                if path.startswith("/"):
                    start = ""
                else:
                    start = f" from group {self.path}"

                raise KeyError(
                    f"Invalid path {path!r}{start}: "
                    f"{current.variables[part].path} is a variable "
                    "and cannot have children"
                )
            else:
                if path.startswith("/"):
                    start = ""
                else:
                    start = f" from group {self.path}"

                raise KeyError(
                    f"Invalid path {path!r}{start}: Path element {part!r} "
                    f"not found in group {current.path}"
                )

        return current

    def __iter__(self):
        """The variables and sub-groups."""
        return chain(self.groups, self.variables)

    def __len__(self):
        """The number of variables and sub-groups."""
        return len(self.variables) + len(self.groups)

    def __repr__(self):
        pd = "" if len(self.dimensions) == 1 else "s"
        pv = "" if len(self.variables) == 1 else "s"
        pg = "" if len(self.groups) == 1 else "s"

        return (
            f"{self.name}: <{__package__}.{self.__class__.__name__}: "
            f"{self.path}, "
            f"{len(self.dimensions)} dimension{pd}, "
            f"{len(self.variables)} variable{pv}, "
            f"{len(self.groups)} group{pg}>"
        )

    def __str__(self):
        return self.dump(display=False, data=False, depth=0, _structure=True)

    def _create_dimension(self, name, size, isunlimited):
        """Create a new dimension in this group.

        :Parameters:

             Parameters *name*, *size*, and *isunlimited* are
             identical those parameters for `Dimension.__init__`.

        :Returns:

            `Dimension`
                The new dimension.

        """
        dimension = self.__Dimension(name, size, isunlimited, self)
        self._dimensions[name] = dimension
        return dimension

    def _create_group(self, name, grp, grp_attrs):
        """Create a new sub-group in this group.

        :Parameters:

             Parameters *name*, *grp*, and *grp_attrs* are identical
             those parameters for `Group.__init__`.

        :Returns:

            `Group`
                The new group.

        """
        group = self.__Group(name, self, self.root, grp, grp_attrs)
        self._groups[name] = group
        return group

    def _create_variable(self, name, var, var_attrs, shape=None):
        """Create a new variable in this group.

        :Parameters:

             Parameters *name*, *var*, *var_attrs*, and *shape* are
             identical those parameters for `Variable.__init__`.

        :Returns:

            `Variable`
                The new variable.

        """
        variable = self.__Variable(name, self, var, var_attrs, shape)
        self._variables[name] = variable
        return variable

    def _populate_all(self):
        """Populate the 'all_*' dictionaries.

        Populates the root group's dictionaries of all dimensions,
        variables, and groups.

        """
        root = self.root

        if self.is_root:
            # Initialise the 'all_*' dictionaries on the root group
            root._all_dimensions = {}
            root._all_variables = {}
            root._all_groups = {}

        for dimension in self._dimensions.values():
            root._all_dimensions[dimension.path] = dimension

        for variable in self._variables.values():
            root._all_variables[variable.path] = variable

        root._all_groups[self.path] = self

        # Recursively populate from sub-groups
        for group in self.groups.values():
            group._populate_all()

    def _parse_group_structure(self):
        """Parse the group structure.

        Parses variables, dimensions, and subgroups, recursively.

        :Parameters:

            root: `Dataset`
                The root group.

        :Returns:

            `None`

        """
        match self.backend_api:
            case "pyfive" | "h5py" | "ppfive":
                hdf5_parse_group_structure(self)

            case "netCDF4":
                netCDF4_parse_group_structure(self)

            case "netcdf_file":
                netcdf_file_parse_group_structure(self)

            case "zarr":
                zarr_parse_group_structure(self)

            case "xarray":
                xarray_parse_group_structure(self)

            case _:
                raise NotImplementedError(
                    "Need a '*_parse group structure' function for "
                    f"backend API {self.backend_api!r}"
                )

    @property
    def backend_accessor(self):
        """The backend object that accesses the group.

        The backend accessor is the interface to the dataset.

        .. seealso:: `backend_library`, `dataset`

        :Returns:

                The backend object.

        """
        return self._grp

    @property
    def dimensions(self):
        """The dimensions defined in this group.

        .. seealso:: `variables`, `groups`

        :Returns:

            `dict`
                The `Dimension` objects, keyed by their names
                realitive to the group.

        :Examples:

        >>> n.dimensions
        {'bounds2': <xnetcdf.Dimension: /bounds2, size=2>}

        """
        return self._dimensions

    @property
    def groups(self):
        """The sub-groups defined in this group.

        .. seealso:: `variables`, `dimensions`

        :Returns:

            `dict`
                The `Group` objects, keyed by their names relative to
                the group.

        :Example:

        >>> n.groups
        {'forecast': <xnetcdf.Group: /forecast, 1 dimension, 2 variables, 1 group>}

        """
        return self._groups

    @property
    def is_root(self):
        """Whether or not this is the root group.

        .. seealso:: `root`

        :Returns:

            `bool`
                `True` if this is the root group, otherwise `False`.

        """
        return self._is_root

    @property
    def name(self):
        """The name of the group in its parent group.

        .. seealso:: `path`

        :Returns:

            `str`
                The relative name (e.g. ``'subgroup'``).

        """
        return self._name

    @property
    def path(self):
        """The absolute path of the group.

        .. seealso:: `name`

        :Returns:

            `str`
                The absolute path of the group, e.g. ``'/'``,
                ``'/model'``, or ``'/group/forecast'``.

        """
        path = getattr(self, "_path", None)
        if path is None:
            if self.is_root:
                path = "/"
            else:
                parent = self.parent
                if parent.is_root:
                    path = f"/{self.name}"
                else:
                    path = f"{parent.path}/{self.name}"

            self._path = path

        return path

    @property
    def variables(self):
        """The variables defined in this group.

        .. seealso:: `dimensions`, `groups`

        :Returns:

            `dict`
                The `Variable` objects, keyed by their names relative
                to the group.

        :Examples:

           >>> n.variables
           {'time': <xnetcdf.Variable: /time, shape=(), dimensions=()>}

        """
        return self._variables

    def dump(
        self,
        display=True,
        data=False,
        depth=None,
        _prefix=None,
        _level=0,
        _structure=False,
    ):
        """A full description of the group.

        .. seealso:: `structure`

        :Parameters:

            display: `bool`, optional
                If False then return the description as a string. By
                default the description is printed.

            data: `bool`, optional
                If True then include a summary of each variable's data
                array. If False (the default) then don't include these
                data summaries.

            depth: `int` or `None`, optional
                Show the structure this many levels into the group
                hierarchy, starting at the current group. If `None`
                (the default), then descend into all sub-groups. If
                `0`, then do not descend into any sub-groups
                (i.e. show only the contents of this group).

        :Returns:

            `None` or `str`
                The description. If *display* is True then the
                description is printed and `None` is
                returned. Otherwise the description is returned as a
                string.

        """
        indent = self._Mixin__indent
        i0 = indent * _level
        i1 = indent * (_level + 1)
        i2 = indent * (_level + 2)

        # _prefix is not currently used
        _prefix = ""

        lines = [f"{i0}{_prefix}{self!r}"]

        # Attributes
        if not _structure and self.attrs:
            printoptions = _printoptions
            if data and "linewidth" not in printoptions:
                # Set the np.printoptions linewidth
                printoptions = printoptions | {"linewidth": len(lines[0])}

            with np.printoptions(**printoptions):
                lines.append(f"{i1}Attributes:")
                lines.extend(
                    f"{i2}{name}: {value!r}"
                    for name, value in self.attrs.items()
                )

        # Dimensions
        if self.dimensions:
            lines.append(f"{i1}Dimensions:")
            lines.extend(
                dim.dump(display=False, _level=_level + 2)
                for name, dim in self.dimensions.items()
            )

        # Variables
        if self.variables:
            lines.append(f"{i1}Variables:")
            lines.extend(
                var.dump(
                    display=False,
                    data=data,
                    _level=_level + 2,
                    _structure=_structure,
                )
                for name, var in self.variables.items()
            )

        # Groups
        if self.groups:
            lines.append(f"{i1}Groups:")
            if depth is None or depth >= self.path.count("/"):
                if depth is not None:
                    depth = depth - 1

                lines.extend(
                    group.dump(
                        display=False,
                        data=data,
                        depth=depth,
                        _level=_level + 2,
                        _structure=_structure,
                    )
                    for group in self.groups.values()
                )
            else:
                lines.extend(
                    f"{i2}{group!r}" for group in self.groups.values()
                )

        out = "\n".join(lines)
        if not display:
            return out

        print(out)

    def is_ancestor_group(self, other):
        """Return True if this group is an ancestor of another group.

        Both groups must have same parent `Dataset` instance. A group
        is considered to be an ancestor of itself.

        If `True`, then *other* is a sub-group of this group.

        :Parameters:

            other: `Group` or `Dataset`
                The group to test against.

        :Returns:

            `bool`
                `True` if this group is an ancestor of *other*, or if
                this group is *other*. `False` otherwise.

        """
        while other is not None:
            if self is other:
                return True

            try:
                other = other.parent
            except AttributeError:
                return False

        return False

    def is_sub_group(self, other):
        """Return True if this group is a subgroup of another group.

        Both groups must have same parent `Dataset` instance. A group
        is considered to be a sub-group of itself.

        :Parameters:

            other: `Group` or `Dataset`
                The group to test against.

        :Returns:

            `bool`
                `True` if this group is a subgroup of *other*, or if
                this group is *other*. `False` otherwise.

        """
        group = self
        while group is not None:
            if group is other:
                return True

            try:
                group = group.parent
            except AttributeError:
                return False

        return False

    def structure(
        self,
        display=True,
        depth=None,
        _prefix=None,
        _level=0,
    ):
        """A purely structural description of the group.

        This similar to `dump`, but no group or variable attributes,
        and no variable data are shown.

        .. seealso:: `dump`

        :Parameters:

            display: `bool`, optional
                If False then return the description as a string. By
                default the description is printed.

            depth: `int` or `None`, optional
                Show the structure this many levels into the group
                hierarchy, starting at the current group. If `None`
                (the default), then descend into all sub-groups. If
                `0`, then do not descend into any sub-groups
                (i.e. show only the contents of this group).

        :Returns:

            `None` or `str`
                The description. If *display* is True then the
                description is printed and `None` is
                returned. Otherwise the description is returned as a
                string.

        """
        return self.dump(
            display=display,
            data=False,
            depth=depth,
            _prefix=_prefix,
            _level=_level,
            _structure=True,
        )


# Set __Group to `Group`, now that `Group` has been defined. This
# references is used to create sub-groups in `Group._create_group`.
Group._Group__Group = Group


class Dataset(Group):
    """A dataset viewed as netCDF.

    A dataset is mapped to a `Dataset` object, which contains netCDF
    groups (`Group` objects), netCDF dimensions (`Dimension` objects),
    netCDF variables (`Variable` objects), and attributes. A variable
    is associated with dimensions and may contain attributes; and a
    group may contain other groups, dimensions, variables, and
    attributes.

    :Backends:

    There is no native capability for directly opening a dataset,
    rather external backend libraries are relied on to read the
    dataset which can then be mapped to the common netCDF view. See
    the *backends* parameter for the supported backends.

    :Dataset formats:

    Supported dataset formats that can be read by at least one of the
    supported backends are: netCDF-4, netCDF-3, Zarr v3, Zarr v2,
    Kerchunk, UK Met Office PP, and UK Met Office fields file.

    :Dataset deinitions:

    See the *dataset* parameter for the different ways in which a
    dataset can be provided.

    :Indexing:

    A group or variable object, anywhere in the group hierarchy, can
    be accessed by indexing an `Dataset` instance with the object's
    name.

    Keys can be provided as an absolute path name or as a path name
    that is relative to the root group. Relative path names may
    include ``.`` and ``..`` elements to indicate positions in the
    group hierarchy. Consecutive ``/`` characters are reduced to a
    single ``/``, and a trailing ``/`` character is always allowed.

    * If the key maps to a group, the `Group` instance is returned.

    * If the key maps to a variable, the `Variable` instance is
      returned.

    :Attributes:

    Attributes are derived from the underlying backend object, and not
    directly from the dataset on disk. An attribute that exists in a
    dataset on disk but has been hidden by the underlying backend
    object will not be available to `xnetcdf`. For instance, a backend
    that follows the CF conventions might remove ``coordinates`` and
    ``bounds`` attributes.

    Attributes that have special structural meanings according to the
    netCDF-4 conventions will not appear in the attribute collection.
    These attributes are ``CLASS``, ``NAME``, ``REFERENCE_LIST``,
    ``DIMENSION_LIST``, ``DIMENSION_LABELS``, and
    ``_ARRAY_DIMENSIONS``, as well as any attributes that start with
    ``_Netcdf4``, ``_nc``, or ``_NC``.

    :Parameters:

        dataset:
            The definition of the netCDF dataset to be read. One of:

            * A string-like path name to the dataset (such as `str` or
              `pathlib.Path` instance)

            * A file-like object that accesses the dataset (such as
              `io.BufferedReader` or the result of an `fsspec` file
              system open)

            * A directory-like object that accesses the dataset (such
              as `fsspec.mapping.FSMap`)

            * Any of the following backend objects (see the *backend*
              parameter) that accesses the dataset: `pyfive.File`,
              `zarr.Group`, `ppfive.File`, `netCDF4.Dataset`,
              `scipy.io.netcdf_file`, `h5py.File`, `xarray.Dataset`,
              and `xarray.DataTree`.

            * Any object ``x`` that accesses the dataset and has the
              same API as one of the allowed backend objects. In
              pratice, this means any object ``x`` for which
              ``isinstance(x, <backend-object>)`` is `True` for any
              ``<backend-object>`` from the selection of allowed
              backend objects. For instance, if you have created a
              library called ``my_pyfive`` for which
              ``my_pyfive.File`` is (registered as) a subclass of
              `pyfive.File`, then ``my_pyfive.File`` instances can be
              passed to `Dataset`.

        backend: `None` or (sequence of) `str`, optional
            Which library to use for opening a string-like, file-like,
            or directory-like dataset. An attempt to read the dataset
            is made by the given backends in the order in which they
            are provided, stopping after the first successful
            read. Performance may be improved by specifiying a backend
            library, because it reduces or removes any unsuccessful
            dataset read attempts, which can be expensive, especially
            for remote datasets.

            By default *backend* is `None`, which is equivalent to
            providing the ordered sequence of backends:

            ``('pyfive', 'zarr' 'ppfive', 'netCDF4', 'netcdf_file',
            'h5py', 'xarray')``

            If the dataset is given as a backend object, then that
            backend must be one of the backends identified by the
            *backend* parameter

            The available backends, and the formats they can read,
            are:

            =================  ======================  ===================
            Backend            Library                 Dataset formats
            =================  ======================  ===================
            ``'pyfive'``       `pyfive`                netCDF-4
            ``'zarr'``         `zarr`                  Zarr, Kerchunk
            ``'ppfive'``       `ppfive`                PP, fields file
            ``'netCDF4'``      `netCDF4`               netCDF-4, netCDF-3
            ``'netcdf_file'``  `scipy.io.netcdf_file`  netCDF-3
            ``'h5py'``         `h5py`                  netCDF-4
            ``'xarray'``       `xarray`                netCDF-4, netCDF-3,
                                                       Zarr, Kerchunk,
                                                       GRIB
            =================  ======================  ===================

            Note that the `xarray` library is itself an interface to
            other backends.

            *Example:*
              To only attempt ``'netCDF4'``: ``'netCDF4'`` or
              ``['netCDF4']``

            *Example:*
              To only attempt ``'netCDF4'`` or ``'pyfive'``, in that
              order: ``('netCDF4', 'pyfive')``

        structural_metadata_strategy: `str`, optional
            The strategy used for retrieving, via the backend library,
            structural metadata from the dataset during the initial
            parsing of the dataset, and caching it. Must be one of:

            * ``'minimal'``

              This is the default. Only the minimum amount of
              structural metadata required to parse the dataset is
              retrieved from the dataset and cached. For instance,
              this includes all variable and group attributes, but may
              exclude (depending on the backend library) the variable
              shapes.

            * ``'maximal'``

              All structural metadata is retrieved from the dataset
              and cached. The dataset then does not need to be
              revisited except to access the variable data arrays.

            Dataset metadata caching can also be applied to an
            existing `Dataset` instance with the
            `cache_structural_metadata` method.

        pyfive_options: `dict` or `None`, optional
            Keyword arguments that are passed to `pyfive.File` when
            opening a dataset with the ``'pyfive'`` backend. Setting
            to `None` (the default) is equivalent to providing an
            empty dictionary. The keyword argument ``mode='r'`` is
            always automatically applied, even when not provided, and
            can't be set to a different value.

        ppfive_options: `dict` or `None`, optional
            Keyword arguments that are passed to `ppfive.File` when
            opening a dataset with the ``'ppfive'`` backend. Setting
            to `None` (the default) is equivalent to providing an
            empty dictionary. The keyword argument ``mode='r'`` is
            always automatically applied, even when not provided, and
            can't be set to a different value.

        netCDF4_options: `dict` or `None`, optional
            Keyword arguments that are passed to `netCDF4.Dataset`
            when opening a dataset with the ``'netCDF4'``
            backend. Setting to `None` (the default) is equivalent to
            providing an empty dictionary. The keyword argument
            ``mode='r'`` is always automatically applied, even when
            not provided, and can't be set to a different value.

        netcdf_file_options: `dict` or `None`, optional
            Keyword arguments that are passed to
            `scipy.io.netcdf_file` when opening a dataset with the
            ``'netcdf_file'`` backend. Setting to `None` (the default)
            is equivalent to providing an empty dictionary. The
            keyword arguments ``mode='r'`` and ``mmap=True`` are
            always automatically applied, even when not provided, and
            can't be set to different values.

        h5py_options: `dict` or `None`, optional
            Keyword arguments that are passed to `h5py.File` when
            opening a dataset with the ``'h5py'`` backend. Setting to
            `None` (the default) is equivalent to providing an empty
            dictionary. The keyword argument ``mode='r'`` is always
            automatically applied, even when not provided, and can't
            be set to a different value.

            It is recommended to set ``rdcc_nbytes``, ``rdcc_w0``, and
            ``rdcc_nslots`` keywords to reduce the risk of poor HDF5
            chunk-access performance with the ``'h5py'`` backend (see
            https://docs.h5py.org/en/stable/high/file.html#chunk-cache
            for details).

        xarray_options: `dict` or `None`, optional
            Keyword arguments that are passed to
            `xarray.open_datatree` when opening a dataset with the
            ``'xarray'`` backend. Setting to `None` (the default) is
            equivalent to providing an empty dictionary. The keyword
            arguments ``mask_and_scale=False, decode_cf=False,
            chunks='auto'`` are always automatically applied, even
            when not provided. The first two arguments can't be set to
            different values, but the third argument (``chunks``) may
            be modified.

        zarr_options: `dict` or `None`, optional
            Keyword arguments that are passed to `zarr.open` when
            opening a dataset with the ``'zarr'`` backend. Setting to
            `None` (the default) is equivalent to providing an empty
            dictionary. The keyword argument ``mode='r'`` is always
            automatically applied, even when not provided, and can't
            be set to a different value.

        zarr_dimension_search: `str`, optional
            How to interpret a Zarr or Kerchunk dataset dimension name
            that contains no group-separator characters, such as
            ``dim`` (as opposed to ``group/dim``, ``/group/dim``,
            ``../dim``, etc.). Ignored for other dataset types.

            For a Zarr or Kerchunk dataset, setting this parameter may
            be necessary for the correct interpretation of the dataset
            in the event that its dimensions are named inconsistently
            with CF conventions (section 2.7 Groups).

            The *zarr_dimension_search* parameter must be one of:

            * ``'closest_ancestor'``

              This is the default and is the behaviour defined by the
              CF conventions (section 2.7 Groups).

              Assume that the sub-group dimension is the same as the
              dimension with the same name and size in an ancestor
              group, if one exists. If multiple such dimensions exist,
              then the correspondence is with the dimension in the
              ancestor group that is **closest** to the sub-group
              (i.e. that is furthest away from the root group).

            * ``'furthest_ancestor'``

              This behaviour is different to that defined by the CF
              conventions (section 2.7 Groups).

              Assume that the sub-group dimension is the same as the
              one with the same name and size in an ancestor group, if
              one exists. If multiple such dimensions exist, then the
              correspondence is with the dimension in the ancestor
              group that is **furthest away** from the sub-group
              (i.e. that is closest to the root group).

            * ``'local'``

              This behaviour is different to that defined by the CF
              conventions (section 2.7 Groups).

              Assume that the sub-group dimension is different to any
              with the same name and size in all ancestor groups.

        verbose: `int`, optional
            Set the verbosity. If *verbose* is ``0`` there is no
            verbose output, and more output is produced for
            progressively larger values of *verbose*. Values of ``5``
            and higher, and the special value ``-1``, produce the same
            maximally verbose output.

    """

    def __init__(
        self,
        dataset,
        backend=None,
        structural_metadata_strategy="minimal",
        pyfive_options=None,
        ppfive_options=None,
        h5py_options=None,
        netCDF4_options=None,
        netcdf_file_options=None,
        xarray_options=None,
        zarr_options=None,
        zarr_dimension_search="closest_ancestor",
        verbose=0,
    ):
        # Options for the different backend read functions
        read_options = {}
        if pyfive_options:
            read_options["pyfive"] = pyfive_options

        if zarr_options:
            read_options["zarr"] = zarr_options

        if xarray_options:
            read_options["xarray"] = xarray_options

        if ppfive_options:
            read_options["ppfive"] = ppfive_options

        if netCDF4_options:
            read_options["netCDF4"] = netCDF4_options

        if netcdf_file_options:
            read_options["netcdf_file"] = netcdf_file_options

        if h5py_options:
            read_options["h5py"] = h5py_options

        self._zarr_dimension_search = zarr_dimension_search

        # Initialise the log of how the dataset was/wasn't read by
        # each backend
        self._dataset_read_log = []

        self._dataset = dataset

        if backend is None:
            read_functions = _read_functions
        else:
            # Restrict the reading to selected backends
            if isinstance(backend, str):
                backend = (backend,)

            try:
                read_functions = {b: _read_functions[b] for b in backend}
            except KeyError as error:
                raise ValueError(
                    f"Invalid backend. Got {error!r}. Valid backends are "
                    f"{tuple(_read_functions)}"
                )

        nc = None
        for backend, func in read_functions.items():
            options = read_options.get(backend, {})
            try:
                nc = func(dataset, options)
            except Exception as error:
                self._dataset_read_log.append(
                    f"{backend}: {error.__class__.__name__}: {error}"
                )
            else:
                message = (
                    "Successfully read"
                    if nc["owns_accessor"]
                    else "Using existing object"
                )
                self._dataset_read_log.append(
                    f"{backend}: {message} {dataset!r}"
                )
                break

        if nc is None:
            # Failed to read dataset
            try:
                # Rewind file-like
                dataset.seek(0)
            except Exception:
                pass

            raise NetCDFError(
                f"Can't read {dataset!r} with any of the backends "
                f"{tuple(read_functions)}:\n\n"
                f"{self.dataset_read_log(display=False)}"
            )

        # Cache the backend, library, dataset, and dataset name
        self._backend_library = nc["library"]
        self._owns_accessor = nc["owns_accessor"]
        self._backend_api = nc["backend_api"]
        self._dataset_name = nc["dataset_name"]

        # Cache the file system protocol, but only if we've found out
        # what it is, and whether or not the dataset exists in the
        # local file system. A value of -1 is a non-string and
        # non-None code for an unknown file system protocol.
        protocol = -1
        protocol = nc["protocol"]
        if protocol == -1:
            is_local = None
        else:
            if isinstance(protocol, (tuple, list)):
                protocol = protocol[0]

            if protocol in ("", "file", "local", None):
                protocol = "file"
                is_local = True
            else:
                is_local = False

            self._protocol = protocol

        self._is_local = is_local

        # ------------------------------------------------------------
        # Parse the group structure
        # ------------------------------------------------------------
        super().__init__(
            name="",
            parent=None,
            root=self,
            grp=nc["nc"],
            grp_attrs=nc["attrs"],
        )

        # Cache the requested amount of structural metadata (after the
        # group structure has been parsed)
        self.cache_structural_metadata(structural_metadata_strategy)

        # Verbose output
        if verbose == -1:
            verbose = 5

        if verbose >= 1:
            log = self.dataset_read_log(display=False)
            if log:
                print(log, "\n")

            if verbose == 1:
                print(repr(self))
            elif verbose == 2:
                print(self)
            elif verbose == 3:
                self.structure()
            elif verbose == 4:
                self.dump()
            elif verbose >= 5:
                self.dump(data=True)

    def __enter__(self):
        """Returns the `Dataset` instance."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Closes the `Dataset` instance with `close`."""
        self.close()

    def __repr__(self):
        pd = "" if len(self.dimensions) == 1 else "s"
        pv = "" if len(self.variables) == 1 else "s"
        pg = "" if len(self.groups) == 1 else "s"

        dataset_name = self.dataset_name
        if dataset_name != "":
            dataset_name = f"{dataset_name}: "

        return (
            f"{dataset_name}<{__package__}.{self.__class__.__name__}: /, "
            f"{len(self.dimensions)} dimension{pd}, "
            f"{len(self.variables)} variable{pv}, "
            f"{len(self.groups)} group{pg}>"
        )

    @property
    def all_dimensions(self):
        """A dictionary of all dimensions in the group hierarchy.

        .. seealso:: `dimensions`, `all_variables`, `all_groups`

        :Returns:

            `dict`
                The dimensions are keyed by their absolute paths.

        :Examples:

        >>> n.all_dimensions
        {'/bounds2': <xnetcdf.Dimension: /bounds2, size=2>,
         '/forecast/lon': <xnetcdf.Dimension: /forecast/lon, size=8, unlimited>,
         '/forecast/model/lat': <xnetcdf.Dimension: /forecast/model/lat, size=5>}

        """
        if not hasattr(self, "_all_dimensions"):
            self._populate_all()

        return self._all_dimensions

    @property
    def all_groups(self):
        """A dictionary of all groups in the group hierarchy.

        .. seealso:: `groups`, `all_dimensions`, `all_variables`

        :Returns:

            `dict`
                The groups are keyed by their absolute paths.

        :Examples:

        >>> n.all_groups
        {'/': <xnetcdf.Dataset: 1 dimension, 1 variable, 1 group>,
         '/forecast': <xnetcdf.Group: /forecast, 1 dimension, 2 variables, 1 group>,
         '/forecast/model': <xnetcdf.Group: /forecast/model, 1 dimension, 3 variables, 0 groups>}

        """
        if not hasattr(self, "_all_groups"):
            self._populate_all()

        return self._all_groups

    @property
    def all_variables(self):
        """A dictionary of all variables in the group hierarchy.

        .. seealso:: `variables`, `all_dimensions`, `all_groups`

        :Returns:

            `dict`
                The variables are keyed by their absolute paths.

        :Examples:

        >>> n.all_variables
        {'/time': <xnetcdf.Variable: /time, shape=(), dimensions=()>,
         '/forecast/lon_bnds': <xnetcdf.Variable: /forecast/lon_bnds, shape=(8, 2), dimensions=(/forecast/lon, /bounds2)>,
         '/forecast/lon': <xnetcdf.Variable: /forecast/lon, shape=(8,), dimensions=(/forecast/lon,)>,
         '/forecast/model/lat_bnds': <xnetcdf.Variable: /forecast/model/lat_bnds, shape=(5, 2), dimensions=(/forecast/model/lat, /bounds2)>,
         '/forecast/model/lat': <xnetcdf.Variable: /forecast/model/lat, shape=(5,), dimensions=(/forecast/model/lat,)>,
         '/forecast/model/q': <xnetcdf.Variable: /forecast/model/q, shape=(5, 8), dimensions=(/forecast/model/lat, /forecast/lon)>}

        """
        if not hasattr(self, "_all_variables"):
            self._populate_all()

        return self._all_variables

    @property
    def backend_accessor(self):
        """The backend object that accesses the dataset.

        The backend accessor is the interface to the dataset.

        .. seealso:: `backend_library`, `dataset`

        :Returns:

                The backend object.

        """
        return self._grp

    def cache_structural_metadata(self, strategy="maximal"):
        """Cache structural metadata from the dataset.

        Any metadata that is already cached is not re-retrieved from
        the dataset.

        Metadata may have already been cached within the backend
        library, in which case retrieving and caching it in the
        `Dataset` instance it may by fast.

        :Parameters:

            strategy: `str`
                The strategy used for caching, via the backend
                library, metadata from the dataset. Must be one of:

                * ``'maximal'``

                  This is the default. All required metadata is
                  retrieved from the dataset and cached. The dataset
                  then does not ever need to revisited except to
                  access the variable data arrays.

                * ``'minimal'``

                  Only the minimum amount of metadata required to
                  parse the dataset is retrieved from the dataset and
                  cached. For instance, this includes all variable and
                  group attributes, but may exclude (depending on the
                  backend library)s the variable shapes. Minimal
                  metadata caching is always applied during `Dataset`
                  instantiation, so there is no benefit in using this
                  option.

        :Returns:

            `None`

        """
        if strategy == "minimal":
            # Minimal caching is already done in `Dataset.__init__`
            return

        if strategy == "maximal":
            # Execute `Variable` methods that might access the dataset and
            # which have not already been run via `Variable.__init__`.
            for variable in self.all_variables.values():
                variable.__orthogonal_indexing__
                variable.dtype
                variable.shape
                variable.shards
                variable.get_dims()
                variable.chunking()
        else:
            raise ValueError(
                f"Invalid value for structural_metadata_strategy. "
                f"Got {strategy!r}, expected one of 'minimal', 'maximal'"
            )

    def close(self):
        """Close the dataset.

        Closes the underlying netCDF dataset, but only if owned by
        this `Dataset` instance.

        :Returns:

            `None`

        """
        if not self._owns_accessor:
            return

        if self.backend_api == "netcdf_file":
            netcdf_file_close(self)
        else:
            try:
                self._grp.close()
            except AttributeError:
                pass

    def dataset_read_log(self, display=True):
        """The dataset-read log.

        .. seealso:: `backend_library`, `backend_api`,
                     `backend_accessor`

        :Parameters:

            display: `bool`, optional
                If False then return the log as a string. By default
                the log is printed.

        :Returns:

            `None` or `str`
                The dataset-read log. If *display* is True then the
                log is printed and `None` is returned. Otherwise the
                log is returned as a string.

        :Examples:

        >>> nc = xnetcdf.Dataset('test.zarr3/')
        >>> nc.dataset_read_log()
        pyfive: IsADirectoryError: [Errno 21] Is a directory: 'test.zarr3/'
        zarr: Successfully read 'test.zarr3/'

        """
        log = "\n".join(self._dataset_read_log)
        if not display:
            return log

        print(log)

    def ncdump(self, display=True):
        """A text CDL description of the dataset.

        The text representation is CDL (network Common Data form
        Language), and emulates the output of ``$ ncdump -h``.

        .. seealso:: `dump`, `structure`

        :Parameters:

            display: `bool`, optional
                If False then return the CDL description as a
                string. By default the description is printed.

        :Returns:

            `None` or `str`
                The CDL description. If *display* is True then the
                description is printed and `None` is
                returned. Otherwise the description is returned as a
                string.

        """
        dataset_name = self.dataset_name
        if dataset_name:
            dataset_name += " "

        lines = []
        lines.append(f"netcdf {dataset_name}{{")
        cdl_format(self, lines)
        lines.append("}")

        out = "\n".join(lines)
        if not display:
            return out

        print(out)
