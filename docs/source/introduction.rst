Introduction
============

Overview
--------

`xnetcdf` is a Python open source library for representing datasets,
in a variety of formats and accessed through diverse Python backends,
with a common netCDF view.

A dataset format can be one of :ref:`many formats <Dataset-formats>`
that can be logically mapped to the `netCDF Enhanced Data Model
<https://docs.unidata.ucar.edu/netcdf-c/current/netcdf_data_model.html>`_.

A dataset is mapped to an `xnetcdf.Dataset` object, which contains
netCDF groups (`xnetcdf.Group` objects), netCDF dimensions
(`xnetcdf.Dimension` objects), netCDF variables (`xnetcdf.Variable`
objects), and attributes. A variable is associated with dimensions and
may contain attributes; and a group may contain sub-groups,
dimensions, variables, and attributes.

Backends
^^^^^^^^

`xnetcdf` has no native capability for directly opening a dataset,
rather external backend libraries are relied on to read the dataset
which can then be mapped to the common netCDF view.

`xnetcdf` supports the following backends for giving access to a
dataset:

- `pyfive`
- `zarr`
- `umfive`
- `netCDF4`
- `scipy.io.netcdf_file`
- `h5py`
- `xarray`

By default, `xnetcdf` will attempt to open a dataset with each of
these backends in turn, in the order given above, returning the
`xnetcdf.Dataset` object from the first successful read.

.. note:: It is not a problem , in general, if a backend library is
          not :ref:`installed <Installation>` -- it just restricts the
          the pool of backends that are available for reading a
          dataset.

Dataset formats
^^^^^^^^^^^^^^^
Supported dataset formats that can be read by at least one of the
supported backends (shown in brackets) are:

- `netCDF-4
  <https://docs.unidata.ucar.edu/nug/current/netcdf_introduction.html>`_
  (`pyfive`, `zarr`, `netCDF4`, `h5py`, `xarray`)
- `netCDF-3
  <https://docs.unidata.ucar.edu/nug/current/netcdf_introduction.html>`_
  (`netCDF4`, `scipy.io.netcdf_file`)
- `Zarr v3
  <https://zarr-specs.readthedocs.io/en/latest/specs.html>`_
  (`zarr`, `xarray`)
- `Zarr v2 <https://zarr-specs.readthedocs.io/en/latest/v2/v2.0.html>`_ 
  (`zarr`, `netCDF4`, `xarray`)
- `Kerchunk <https://fsspec.github.io/kerchunk>`_ (`zarr`, `xarray`)
- `GRIB
  <https://community.wmo.int/site/knowledge-hub/programmes-and-initiatives/wmo-information-system-wis/about-manual-codes-volume-i2>`_
  (`xarray`)
- `UK Met Office PP
  <https://artefacts.ceda.ac.uk/badc_datadocs/um/umdp_F3-UMDPF3.pdf>`_
  (`umfive`)
- `UK Met Office fields file
  <https://artefacts.ceda.ac.uk/badc_datadocs/um/umdp_F3-UMDPF3.pdf>`_
  (`umfive`)

Dataset definitions
^^^^^^^^^^^^^^^^^^^

A dataset can be passed to `xnetcdf.Dataset` with one of the following
dataset definitions:

- A string-like path name to the dataset (such as `str` or
  `pathlib.Path` instance).
  
- A file-like object that accesses the dataset (such as
  `io.BufferedReader` or the result of an `fsspec` file system open)

- A directory-like object that accesses the dataset (such as
  `fsspec.mapping.FSMap`)

- Any of the following allowed backend objects that accesses the
  dataset: `pyfive.File`, `zarr.Group`, `umfive.File`,
  `netCDF4.Dataset`, `scipy.io.netcdf_file`, `h5py.File`,
  `xarray.Dataset`, and `xarray.DataTree`.

- Any object ``x`` that accesses the dataset and has the same API as
  one of the allowed backend objects. In pratice, this means any
  object ``x`` for which ``isinstance(x, <backend-object>)`` is `True`
  for any ``<backend-object>`` from the selection of allowed backend
  objects. For instance, if you have created a library called
  ``my_pyfive`` for which ``my_pyfive.File`` is (registered as) a
  subclass of `pyfive.File`, then ``my_pyfive.File`` instances can be
  passed to `xnetcdf.Dataset`.

A simple example
----------------
    
An example of how to use `xnetcdf` to open a dataset and inspect its
contents:

.. code-block:: python

   >>> import xnetcdf
   >>> nc = xnetcdf.Dataset('path/to/your/dataset')  # Open the dataset
   >>> print(nc)  # Inspect the dataset contents
   path/to/your/dataset: <xnetcdf.Dataset: /, 3 dimensions, 6 variables, 0 groups>
       Dimensions:
           lat: <xnetcdf.Dimension: /lat, size=5>
           bounds2: <xnetcdf.Dimension: /bounds2, size=2>
           lon: <xnetcdf.Dimension: /lon, size=8>
       Variables:
           lat_bnds: <xnetcdf.Variable: /lat_bnds, shape=(5, 2), dimensions=(/lat, /bounds2)>
           lat: <xnetcdf.Variable: /lat, shape=(5,), dimensions=(/lat,)>
           lon_bnds: <xnetcdf.Variable: /lon_bnds, shape=(8, 2), dimensions=(/lon, /bounds2)>
           lon: <xnetcdf.Variable: /lon, shape=(8,), dimensions=(/lon,)>
           time: <xnetcdf.Variable: /time, shape=(), dimensions=()>
           q: <xnetcdf.Variable: /q, shape=(5, 8), dimensions=(/lat, /lon)>
   >>> nc['lat'].attrs  # Get a variable's attributes
   {'bounds': 'lat_bnds',
    'standard_name': 'latitude',
    'units': 'degrees_north'}
   >>> nc['lat'][...]  # Get a variable's data array
   array([-75., -45.,   0.,  45.,  75.])

The dataset is presented in terms of netCDF groups, dimensions and
variables (there is only the root group in this example), which can
contain attributes and data arrays.

See :ref:`Quick-start` for more examples.

The `xnetcdf` API
-----------------

The `xnetcdf` API has been designed to be "largely consistent" with
the APIs of `netCDF4`, `pyfive` and `h5netcdf`. This means that, while
`xnetcdf` can't be used as a perfect drop-in for any of these three
libraries, most attributes and methods of each one of them can be
found in `xnetcdf`, and with the same behaviour.

For instance, `xnetcdf.Variable` instances have a
`~xnetcdf.Variable.chunks` attribute and a
`~xnetcdf.Variable.chunking` method -- the former is also found in the
`pyfive` and `h5netcdf` libraries, the latter in the `netCDF4`
library.

Performance
-----------

`xnetcdf` is "structure- and attribute-eager", meaning that during
`xnetcdf.Dataset` instantiation, the minimum amount of metadata
required to parse the entire netCDF group, variable, and dimension
structure is brought into memory and cached. This includes all group
and variable attributes.

Some `xnetcdf.Variable` and `xnetcdf.Group` attributes and methods
might also access the underlying backend for structural metadata that
is not necessary for parsing the dataset. In this case, the metadata
is also cached for future use. (Note that these extra structural
metadata can also be cached at instantiation time -- see the
``structural_metadata_strategy`` parameter to `xnetcdf.Dataset`)

:ref:`Variable data array access <Variable-data-and-indexing>` is
always via the underlying backend library, and therefore if that
library supports lazy data array access (which all of the supported
backends do), then so will the `xnetcdf.Variable` instance.
