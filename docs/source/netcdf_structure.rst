NetCDF structure
================

This page summarizes how the `xnetcdf` classes represent the netCDF
structure in terms of the dataset, groups, variables, dimensions, and
attributes.

The examples use the ``test.nc`` dataset (`download 28 KB
<https://raw.githubusercontent.com/NCAS-CMS/xnetcdf/main/tests/data/test.nc>`_). Example
datasets in other formats can be found `here
<https://github.com/NCAS-CMS/xnetcdf/tree/main/tests/data>`_.

----

.. _NetCDF-dataset:

NetCDF dataset
--------------

A netCDF dataset is mapped to an `xnetcdf.Dataset` object, which
contains :ref:`netCDF groups <NetCDF-group>`, :ref:`netCDF dimensions
<NetCDF-dimension>`, :ref:`netCDF variables <NetCDF-variable>`, and
attributes.

.. _Dataset-definition:

Dataset definition
^^^^^^^^^^^^^^^^^^

The original dataset definition used to instantiate an
`xnetcdf.Dataset` is available with the `~xnetcdf.Dataset.dataset`
attribute, and the name of the dataset is accessed with the
`~xnetcdf.Dataset.dataset_name` attribute.

.. code-block:: python
   :caption: Example

   >>> import xnetcdf
   >>> nc = xnetcdf.Dataset('test.nc')  # Open the dataset defined by its name
   >>> nc
   test.nc: <xnetcdf.Dataset: /, 1 dimension, 1 variable, 1 group>
   >>> nc.dataset
   'test.nc'
   >>> nc.dataset_name
   'test.nc'

.. code-block:: python
   :caption: Example

   >>> import xnetcdf
   >>> import fsspec
   >>> file_like = fsspec.filesystem('file').open('tests.nc', 'rb')
   >>> nc = xnetcdf.Dataset(file_like)  # Open the dataset defined by a file-like object
   >>> nc.dataset
   <fsspec.implementations.local.LocalFileOpener at 0x77dd421ac1f0>
   >>> nc.dataset is file_like
   True
   >>> nc.dataset_name
   'test.nc'

.. _Dataset-backend:

Dataset backend
^^^^^^^^^^^^^^^

The backend library and and the backend object that is accessing the
dataset are availabl via the `xnetcdf.Dataset` attributes
`~xnetcdf.Dataset.backend_library` and
`~xnetcdf.Dataset.backend_accessor` repsectively.

.. code-block:: python
   :caption: Example

   >>> import xnetcdf
   >>> nc = xnetcdf.Dataset('test.nc')  # Open the dataset
   >>> nc
   test.nc: <xnetcdf.Dataset: /, 1 dimension, 1 variable, 1 group>
   >>> nc.backend_library
   <module 'pyfive' from 'pyfive/pyfive/__init__.py'>
   >>> nc.backend_accessor
   <HDF5 file "test.nc" (mode r)>

A log of which backend libraries were used, successfully or
unsuccessfuly, to read the data set is available with the
`~xnetcdf.Dataset.dataset_read_log` method.
   
.. _Dataset-indexing:

Dataset indexing
^^^^^^^^^^^^^^^^

A group or variable object, anywhere in the group hierarchy, can be
accessed by indexing an `xnetcdf.Dataset` instance with the object's
name.

The name can be provided as an absolute path name or a path name that
is relative to the root group. Relative path names may include ``.``
and ``..`` elements to indicate positions in the group
hierarchy. Consecutive ``/`` characters are reduced to a single ``/``,
and a trailing ``/`` character is always allowed.

.. code-block:: python
   :caption: Example

   >>> import xnetcdf
   >>> nc = xnetcdf.Dataset('test.nc')  # Open the dataset
   >>> nc
   test.nc: <xnetcdf.Dataset: /, 1 dimension, 1 variable, 1 group>
   >>> nc.attrs  # Get the attributes
   >>> nc['forecast']
   forecast: <xnetcdf.Group: /forecast, 1 dimension, 2 variables, 1 group>
   >>> nc['forecast/model']
   model: <xnetcdf.Group: /forecast/model, 1 dimension, 3 variables, 0 groups>
   >>> nc['time']
   time: <xnetcdf.Variable: /time, shape=(), dimensions=()>
   >>> nc['forecast/lon']
   lon: <xnetcdf.Variable: /forecast/lon, shape=(8,), dimensions=(/forecast/lon,)>
   >>> nc['forecast/model/q']
   q: <xnetcdf.Variable: /forecast/model/q, shape=(5, 8), dimensions=(/forecast/model/lat, /forecast/lon)>
   >>> nc['time'] is nc['/time'] is nc['./time'] is nc['forecast/../time']
   True
   >>> nc['forecast'] is nc['/forecast/model/..']
   True
   >>> nc['./forecast/lon'] is nc['/forecast//model/../lon']
   True

.. _Dataset-attributes:

Dataset attributes
^^^^^^^^^^^^^^^^^^

The attributes of an `xnetcdf.Dataset` instance are accessed with the
`~xnetcdf.Dataset.attrs` attribute.

.. code-block:: python
   :caption: Example

   >>> import xnetcdf
   >>> nc = xnetcdf.Dataset('test.nc')  # Open the dataset
   >>> nc
   test.nc: <xnetcdf.Dataset: /, 1 dimension, 1 variable, 1 group>
   >>> nc.attrs  # Get the attributes
   {'Conventions': 'CF-1.13',
    'global_attr_1': np.float64(3.14),
    'global_attr_2': 'foo'}

Attributes are derived from the underlying backend object, and not
directly from the dataset on disk. An attribute that exists in a
dataset on disk but has been hidden by the underlying backend object
will not be available to `xnetcdf`. For instance, a backend that
follows the CF conventions might remove ``coordinates`` and ``bounds``
attributes.

Attributes that have special structural meanings according to the
netCDF-4 conventions will not appear in the attribute collection.
These attributes are ``CLASS``, ``NAME``, ``REFERENCE_LIST``,
``DIMENSION_LIST``, ``DIMENSION_LABELS``, and ``_ARRAY_DIMENSIONS``,
as well as any attributes that start with ``_Netcdf4``, ``_nc``, or
``_NC``.

.. _Dataset-groups:

Dataset groups
^^^^^^^^^^^^^^

The groups of an `xnetcdf.Dataset` instance are accessed with the
`~xnetcdf.Dataset.groups` and `~xnetcdf.Dataset.all_groups`
attributes. The former returns the the `xnetcdf.Group` objects defined
in the root group, and the latter returns all `xnetcdf.Group` objects
wherever they appear in the group hierarchy.

.. code-block:: python

   >>> import xnetcdf
   >>> nc = xnetcdf.Dataset('test.nc')  # Open the dataset
   >>> nc
   test.nc: <xnetcdf.Dataset: /, 1 dimension, 1 variable, 1 group>
   >>> nc.groups  # Get the groups defined in the root group
   {'forecast': forecast: <xnetcdf.Group: /forecast, 1 dimension, 2 variables, 1 group>}
   >>> nc.all_groups  # Get all groups
   {'/': /home/david/xnetcdf/tests/data/test.nc: <xnetcdf.Dataset: /, 1 dimension, 1 variable, 1 group>,
    '/forecast': forecast: <xnetcdf.Group: /forecast, 1 dimension, 2 variables, 1 group>,
    '/forecast/model': model: <xnetcdf.Group: /forecast/model, 1 dimension, 3 variables, 0 groups>}

.. _Dataset-variables:

Dataset variables
^^^^^^^^^^^^^^^^^

The variables of an `xnetcdf.Dataset` instance are accessed with the
`~xnetcdf.Dataset.variables` and `~xnetcdf.Dataset.all_variables`
attributes. The former returns the `xnetcdf.Variable` objects defined
in the root group, and the latter returns all `xnetcdf.Variable`
objects wherever they appear in the group hierarchy.

.. code-block:: python
   :caption: Example

   >>> import xnetcdf
   >>> nc = xnetcdf.Dataset('test.nc')  # Open the dataset
   >>> nc
   test.nc: <xnetcdf.Dataset: /, 1 dimension, 1 variable, 1 group>
   >>> nc.variables  # Get the variables defined in the root group
   {'time': time: <xnetcdf.Variable: /time, shape=(), dimensions=()>}
   >>> nc.all_variables  # Get all variables
   {'/time': time: <xnetcdf.Variable: /time, shape=(), dimensions=()>,
    '/forecast/lon_bnds': lon_bnds: <xnetcdf.Variable: /forecast/lon_bnds, shape=(8, 2), dimensions=(/forecast/lon, /bounds2)>,
    '/forecast/lon': lon: <xnetcdf.Variable: /forecast/lon, shape=(8,), dimensions=(/forecast/lon,)>,
    '/forecast/model/lat_bnds': lat_bnds: <xnetcdf.Variable: /forecast/model/lat_bnds, shape=(5, 2), dimensions=(/forecast/model/lat, /bounds2)>,
    '/forecast/model/lat': lat: <xnetcdf.Variable: /forecast/model/lat, shape=(5,), dimensions=(/forecast/model/lat,)>,
    '/forecast/model/q': q: <xnetcdf.Variable: /forecast/model/q, shape=(5, 8), dimensions=(/forecast/model/lat, /forecast/lon)>}

.. _Dataset-dimensions:

Dataset dimensions
^^^^^^^^^^^^^^^^^^

The dimensions of an `xnetcdf.Dataset` instance are accessed with the
`~xnetcdf.Dataset.dimensions` and `~xnetcdf.Dataset.all_dimensions`
attributes. The former returns the `xnetcdf.Dimension` objects defined
in the root group, and the latter returns all `xnetcdf.Dimension`
objects wherever they appear in the group hierarchy.

.. code-block:: python
   :caption: Example

   >>> import xnetcdf
   >>> nc = xnetcdf.Dataset('test.nc')  # Open the dataset
   >>> nc
   test.nc: <xnetcdf.Dataset: /, 1 dimension, 1 variable, 1 group>
   >>> nc.dimensions  # Get the dimensions defined in the root group
   {'bounds2': bounds2: <xnetcdf.Dimension: /bounds2, size=2>}
   >>> nc.all_dimensions  # Get all dimensions		
   {'/bounds2': bounds2: <xnetcdf.Dimension: /bounds2, size=2>,
    '/forecast/lon': lon: <xnetcdf.Dimension: /forecast/lon, size=8, unlimited>,
    '/forecast/model/lat': lat: <xnetcdf.Dimension: /forecast/model/lat, size=5>}

----

.. _NetCDF-group:

NetCDF group
------------

A netCDF group is mapped to an `xnetcdf.Group` object, which contains
:ref:`netCDF dimensions <NetCDF-dimension>`, :ref:`netCDF variables
<NetCDF-variable>`, further netCDF groups, and attributes.

.. _Group-name:

Group name
^^^^^^^^^^

The name of an `xnetcdf.Group` instance is accessed with the
`~xnetcdf.Group.name` and `~xnetcdf.Group.path` attributes, providing
the name relative to the parent group and the absolute path name
respectively.

.. code-block:: python
   :caption: Example

   >>> import xnetcdf
   >>> nc = xnetcdf.Group('test.nc')  # Open the dataset
   >>> nc
   test.nc: <xnetcdf.Dataset: /, 1 dimension, 1 variable, 1 group>
   >>> g = nc['forecast/model']  # Select a group
   >>> g
   forecast: <xnetcdf.Group: /forecast, 1 dimension, 2 variables, 1 group>
   >>> g.name
   'model'
   >>> g.path
   '/forecast/model'

.. _Group-indexing:

Group indexing
^^^^^^^^^^^^^^

A group or variable object, anywhere in the group hierarchy, can be
accessed by indexing an `xnetcdf.Group` instance with the object's
name.

The name can be provided as an absolute path name or a path name that
is relative to the root group. Relative path names may include ``.``
and ``..`` elements to indicate positions in the group
hierarchy. Consecutive ``/`` characters are reduced to a single ``/``,
and a trailing ``/`` character is always allowed.

.. code-block:: python
   :caption: Example

   >>> import xnetcdf
   >>> nc = xnetcdf.Dataset('test.nc')  # Open the dataset
   >>> nc
   test.nc: <xnetcdf.Dataset: /, 1 dimension, 1 variable, 1 group>
   >>> g = nc['forecast']  # Select a group
   >>> g
   forecast: <xnetcdf.Group: /forecast, 1 dimension, 2 variables, 1 group>
   >>> g['model']
   model: <xnetcdf.Group: /forecast/model, 1 dimension, 3 variables, 0 groups>
   >>> g['lon']
   lon: <xnetcdf.Variable: /forecast/lon, shape=(8,), dimensions=(/forecast/lon,)>
   >>> g['..']
   /home/david/xnetcdf/tests/data/test.nc: <xnetcdf.Dataset: /, 1 dimension, 1 variable, 1 group>
   >>> g['./model/q']
   q: <xnetcdf.Variable: /forecast/model/q, shape=(5, 8), dimensions=(/forecast/model/lat, /forecast/lon)>
   >>> g['/time']
   time: <xnetcdf.Variable: /time, shape=(), dimensions=()>

An `xnetcdf.Dataset` that contains the root group is also an
`xnetcdf.Group` instance, so see :ref:`Dataset-indexing` for more
examples.


.. _Group-attributes:

Group attributes
^^^^^^^^^^^^^^^^

The attributes of an `xnetcdf.Group` instance are accessed with the
`~xnetcdf.Group.attrs` attribute.

.. code-block:: python
   :caption: Example

   >>> import xnetcdf
   >>> nc = xnetcdf.Group('test.nc')  # Open the dataset
   >>> g = nc['/forecast/model']  # Select a group
   >>> g
   model: <xnetcdf.Group: /forecast/model, 1 dimension, 3 variables, 0 groups>
   >>> g.attrs  # Get the attributes
   {'group_attr_1': np.int64(12),
    'group_attr_2': 'bar'}

Attributes are derived from the underlying backend object, and not
directly from the dataset on disk. An attribute that exists in a
dataset on disk but has been hidden by the underlying backend object
will not be available to `xnetcdf`. For instance, a backend that
follows the CF conventions might remove ``coordinates`` and ``bounds``
attributes.

Attributes that have special structural meanings according to the
netCDF-4 conventions will not appear in the attribute collection.
These attributes are ``CLASS``, ``NAME``, ``REFERENCE_LIST``,
``DIMENSION_LIST``, ``DIMENSION_LABELS``, and ``_ARRAY_DIMENSIONS``,
as well as any attributes that start with ``_Netcdf4``, ``_nc``, or
``_NC``.

.. _Group-sub-groups:

Group sub-groups
^^^^^^^^^^^^^^^^

The sub-groups of an `xnetcdf.Group` instance are accessed with the
`~xnetcdf.Group.groups` attribute that returns the `xnetcdf.Group`
objects defined in the current group.

.. code-block:: python
   :caption: Example

   >>> import xnetcdf
   >>> nc = xnetcdf.Group('test.nc')  # Open the dataset
   >>> g = nc['/forecast']  # Select a group
   >>> g
   forecast: <xnetcdf.Group: /forecast, 1 dimension, 2 variables, 1 group>
   >>> g.groups  # Get the groups defined in the this group
   {'model': model: <xnetcdf.Group: /forecast/model, 1 dimension, 3 variables, 0 groups>}

.. _Group-variables:

Group variables
^^^^^^^^^^^^^^^

The variables of an `xnetcdf.Group` instance are accessed with the
`~xnetcdf.Group.variables` attribute that returns the
`xnetcdf.Variable` objects defined in the current group.

.. code-block:: python
   :caption: Example

   >>> import xnetcdf
   >>> nc = xnetcdf.Group('test.nc')  # Open the dataset
   >>> g = nc['/forecast']  # Select a group
   >>> g
   forecast: <xnetcdf.Group: /forecast, 1 dimension, 2 variables, 1 group>
   >>> g.variables  # Get the variables defined in the this group
   {'lon_bnds': lon_bnds: <xnetcdf.Variable: /forecast/lon_bnds, shape=(8, 2), dimensions=(/forecast/lon, /bounds2)>,
    'lon': lon: <xnetcdf.Variable: /forecast/lon, shape=(8,), dimensions=(/forecast/lon,)>}

.. _Group-dimensions:

Group dimensions
^^^^^^^^^^^^^^^^

The dimensions of an `xnetcdf.Group` instance are accessed with the
`~xnetcdf.Group.dimensions` attribute that returns the
`xnetcdf.Dimension` objects defined in the current group.

.. code-block:: python
   :caption: Example

   >>> import xnetcdf
   >>> nc = xnetcdf.Group('test.nc')  # Open the dataset
   >>> g = nc['/forecast']  # Select a group
   >>> g
   forecast: <xnetcdf.Group: /forecast, 1 dimension, 2 variables, 1 group>
   >>> nc.dimensions  # Get the dimensions defined in the root group
   {'lon': lon: <xnetcdf.Dimension: /forecast/lon, size=8, unlimited>}

----

.. _NetCDF-variable:

NetCDF variable
---------------

A netCDF variable in a :ref:`netCDF group <NetCDF-group>` is mapped to
an `xnetcdf.Variable` object, which contains attributes and references
to :ref:`netCDF dimensions <NetCDF-dimension>`.

.. _Variable-name:

Variable name
^^^^^^^^^^^^^

The name of an `xnetcdf.Variable` instance is accessed with the
`~xnetcdf.Variable.name` and `~xnetcdf.Variable.path` attributes,
providing the name relative to the parent group and the absolute path
name respectively.

.. code-block:: python
   :caption: Example

   >>> import xnetcdf
   >>> nc = xnetcdf.Group('test.nc')  # Open the dataset
   >>> v = nc['/forecast/model/q']  # Select a variable
   >>> v
   q: <xnetcdf.Variable: /forecast/model/q, shape=(5, 8), dimensions=(/forecast/model/lat, /forecast/lon)>
   >>> v.name
   'q'
   >>> g.path
   '/forecast/model/q'

.. _Variable-data-and-indexing:

Variable data and indexing
^^^^^^^^^^^^^^^^^^^^^^^^^^

The data array of an `xnetcdf.Variable` instance is accessed by direct
indexing, following whatever indexing rules are allowed by the
underlying backend object.

The requested subspace is always returned as a `numpy` array.

.. note:: Since the interpretation of the indices is handled entirely
          by the underlying backend object, the same indices may
          define a different subspace for different underlying
          backends.

.. code-block:: python
   :caption: Example

   >>> import xnetcdf
   >>> nc = xnetcdf.Dataset('test.nc')  # Open the dataset
   >>> v = nc['/forecast/model/q']  # Select a variable
   >>> v
   q: <xnetcdf.Variable: /forecast/model/q, shape=(5, 8), dimensions=(/forecast/model/lat, /forecast/lon)>
   >>> v.shape  # Inspect the data shape
   (5, 8)
   >>> v[...]  # Get the entire data array
   array([[0.007, 0.034, 0.003, 0.014, 0.018, 0.037, 0.024, 0.029],
          [0.023, 0.036, 0.045, 0.062, 0.046, 0.073, 0.006, 0.066],
          [0.11 , 0.131, 0.124, 0.146, 0.087, 0.103, 0.057, 0.011],
          [0.029, 0.059, 0.039, 0.07 , 0.058, 0.072, 0.009, 0.017],
          [0.006, 0.036, 0.019, 0.035, 0.018, 0.037, 0.034, 0.013]],
         dtype=float32)
   >>> q[:,  [1, 3, 2]]  # Get a subspace of the data array
   array([[0.034, 0.014, 0.003],
          [0.036, 0.062, 0.045],
          [0.131, 0.146, 0.124],
          [0.059, 0.07 , 0.039],
          [0.036, 0.035, 0.019]], dtype=float32)

.. _Variable-attributes:

Variable attributes
^^^^^^^^^^^^^^^^^^^

The attributes of an `xnetcdf.Variable` instance are accessed with the
`~xnetcdf.Variable.attrs` attribute.  following whatever indexing
rules are allowed by the underlying backend object.

.. code-block:: python
   :caption: Example

   >>> import xnetcdf
   >>> nc = xnetcdf.Dataset('test.nc')  # Open the dataset
   >>> v = nc['/forecast/lon']  # Select a variable
   >>> v
   lon: <xnetcdf.Variable: /forecast/lon, shape=(8,), dimensions=(/forecast/lon,)>
   >>> v.attrs  # Get the attributes
   {'bounds': '/forecast/lon_bnds',
    'standard_name': 'longitude',
    'units': 'degrees_east'}

Attributes are derived from the underlying backend object, and not
directly from the dataset on disk. An attribute that exists in a
dataset on disk but has been hidden by the underlying backend object
will not be available to `xnetcdf`. For instance, a backend that
follows the CF conventions might remove ``coordinates`` and ``bounds``
attributes.

Attributes that have special structural meanings according to the
netCDF-4 conventions will not appear in the attribute collection.
These attributes are ``CLASS``, ``NAME``, ``REFERENCE_LIST``,
``DIMENSION_LIST``, ``DIMENSION_LABELS``, and ``_ARRAY_DIMENSIONS``,
as well as any attributes that start with ``_Netcdf4``, ``_nc``, or
``_NC``.

.. _Variable-dimensions:

Variable dimensions
^^^^^^^^^^^^^^^^^^^

The dimensions of an `xnetcdf.Variable` instance are accessed with the
`~xnetcdf.Variable.dimensions` and `~xnetcdf.Variable.dimension_paths`
attributes, and the `~xnetcdf.Variable.get_dims` method. The
attributes return the dimension names as relative or absolute path
names respectively. The method returns the `xnetcdf.Dimension`
objects. In each case, the dimension order corresponds to the axes of
the variable's data array.

.. code-block:: python
   :caption: Example

   >>> import xnetcdf
   >>> nc = xnetcdf.Group('test.nc')  # Open the dataset
   >>> v = nc['/forecast/model/q']  # Select a variable
   >>> v
   q: <xnetcdf.Variable: /forecast/model/q, shape=(5, 8), dimensions=(/forecast/model/lat, /forecast/lon)>
   >>> v.dimensions
   ('lat', 'lon')
   >>> v.dimension_paths
   ('/forecast/model/lat', '/forecast/lon')
   >>> v.get_dims()
   (lat: <xnetcdf.Dimension: /forecast/model/lat, size=5>,
    lon: <xnetcdf.Dimension: /forecast/lon, size=8, unlimited>)

.. _Variable-group:

Variable group
^^^^^^^^^^^^^^

The parent group in which the an `xnetcdf.Variable` instance is
defined is accessed with the `~xnetcdf.Variable.group`
method. 

.. code-block:: python
   :caption: Example

   >>> import xnetcdf
   >>> nc = xnetcdf.Group('test.nc')  # Open the dataset
   >>> v = nc['/forecast/model/q']  # Select a variable
   >>> v
   q: <xnetcdf.Variable: /forecast/model/q, shape=(5, 8), dimensions=(/forecast/model/lat, /forecast/lon)>
   >>> v.group()
   model: <xnetcdf.Group: /forecast/model, 1 dimension, 3 variables, 0 groups>

----

.. _NetCDF-dimension:

NetCDF dimension
----------------

A netCDF dimension in a :ref:`netCDF group <NetCDF-group>` is mapped
to an `xnetcdf.Dimension` object.

.. _Dimension-name:

Dimension name
^^^^^^^^^^^^^^

The name of an `xnetcdf.Dimension` instance is accessed with the
`~xnetcdf.Dimension.name` and `~xnetcdf.Dimension.path` attributes,
providing the name relative to the parent group and the absolute path
name respectively.

.. code-block:: python
   :caption: Example

   >>> import xnetcdf
   >>> nc = xnetcdf.Group('test.nc')  # Open the dataset
   >>> d = nc['forecast'].dimensions['lon']  # Select a dimension
   >>> d
   lon: <xnetcdf.Dimension: /forecast/lon, size=8, unlimited>
   >>> d.name
   'lon'
   >>> d.path
   '/forecast/lon'

.. _Dimension-size:

Dimension size
^^^^^^^^^^^^^^

The size of an `xnetcdf.Dimension` instance is accessed with the
`~xnetcdf.Dimension.size` attribute, and the unlimited status is
accessed with the `~xnetcdf.Dimension.isunlimited` method.

.. code-block:: python
   :caption: Example

   >>> import xnetcdf
   >>> nc = xnetcdf.Group('test.nc')  # Open the dataset
   >>> d = nc['forecast'].dimensions['lon']  # Select a dimension
   >>> d
   lon: <xnetcdf.Dimension: /forecast/lon, size=8, unlimited>
   >>> d.group()
   forecast: <xnetcdf.Group: /forecast, 1 dimension, 2 variables, 1 group>
   >>> d.isunlimited()
   True

.. _Dimension-group:

Dimension group
^^^^^^^^^^^^^^^

The parent group in which the an `xnetcdf.Dimension` instance is
defined is accessed with the `~xnetcdf.Dimension.group` method.

.. code-block:: python
   :caption: Example

   >>> import xnetcdf
   >>> nc = xnetcdf.Group('test.nc')  # Open the dataset
   >>> d = nc['forecast'].dimensions['lon']  # Select a dimension
   >>> d
   lon: <xnetcdf.Dimension: /forecast/lon, size=8, unlimited>
   >>> d.group()
   forecast: <xnetcdf.Group: /forecast, 1 dimension, 2 variables, 1 group>
