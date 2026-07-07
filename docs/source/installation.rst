.. _Installation:

Installation
============

The only dependexncy required run the software, besides Python, is
`numpy` (version 2.0.0 or later).

However, each of the backend libraries `pyfive`, 
`netCDF4`, `zarr`, `umfive`, `scipy.io.netcdf_file`, `xarray`, and
`h5py` can only be used if it installed. It is not a problem, in
general, if a backend library is not installed -- it just reduces the
size of the pool of backends that are available for reading a dataset.

`xnetcdf` can be installed using ``pip`` using the command:

.. code-block:: console

    $ pip install xnetcdf

To install with all of the :ref:`backend libraries <Backends>` using
``pip``:

.. code-block:: console

    $ pip install xnetcdf[all]

A ``conda`` package, which also installs all of the backend
libraries is available from conda-forge:

.. code-block:: console

    $ conda install -c conda-forge xnetcdf

The library can also be imported directly from the `xnetcdf` source
root directory:

.. code-block:: console

    $ cd xnetcdf
    $ pip install -e . 
