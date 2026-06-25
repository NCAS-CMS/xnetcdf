[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![DOI](https://zenodo.org/badge/DOI/XX.XXXX/zenodo.XXXXXXX.svg)](https://doi.org/XX.XXXX/zenodo.XXXXXXXX)
[![Documentation Status](https://app.readthedocs.org/projects/xnetcdf/badge/?version=latest)](https://xnetcdf.readthedocs.io/en/latest/?badge=latest)
[![Test](https://github.com/NCAS-CMS/xnetcdf/actions/workflows/pytest.yml/badge.svg)](https://github.com/NCAS-CMS/xnetcdf/actions/workflows/pytest.yml)
[![codecov](https://codecov.io/gh/NCAS-CMS/xnetcdf/graph/badge.svg?token=3In5JuzeGK)](https://codecov.io/gh/NCAS-CMS/xnetcdf)
[![Anaconda-Server Badge](https://anaconda.org/conda-forge/xnetcdf/badges/version.svg)](https://anaconda.org/conda-forge/xnetcdf)


# xnetcdf

## [Read the documentation](https://xnetcdf.readthedocs.io)

`xnetcdf` is a Python open source library for representing datasets,
in a variety of formats and accessed through diverse Python backends,
with a common netCDF view.

A dataset format can be one of many formats that can be logically
mapped to the [netCDF Enhanced Data
Model](https://docs.unidata.ucar.edu/netcdf-c/current/netcdf_data_model.html).

A dataset is mapped to an `xnetcdf.Dataset` object, which contains
netCDF groups (`xnetcdf.Group` objects), netCDF dimensions
(`xnetcdf.Dimension` objects), netCDF variables (`xnetcdf.Variable`
objects), and attributes. A variable is associated with dimensions and
may contain attributes; and a group may contain sub-groups,
dimensions, variables, and attributes.

### Backends

`xnetcdf` has no native capability for directly opening a dataset,
rather external backend libraries are relied on to read the dataset
which can then be mapped to the common netCDF view.

`xnetcdf` supports the following backends for giving access to a
dataset: `pyfive`, `zarr`, `ppfive`, `netCDF4`,
`scipy.io.netcdf_file`, `h5py`, and `xarray`

### Dataset formats

Supported dataset formats that can be read by at least one of the
supported backends are: `netCDF-4`, `netCDF-3`, `Zarr v3`, `Zarr v2`,
`Kerchunk`, `UK Met Office PP`, and `UK Met Office fields file`.

### Dataset definitions

A dataset can be passed to `xnetcdf.Dataset` with one of the following
dataset definitions:

- A string-like path name to the dataset (such as `str` or
  `pathlib.Path` instance).
  
- A file-like object that accesses the dataset (such as
  `io.BufferedReader` or the result of an `fsspec` file system open)

- A directory-like object that accesses the dataset (such as
  `fsspec.mapping.FSMap`)

- Any of the following allowed backend objects that accesses the
  dataset: `pyfive.File`, `zarr.Group`, `xarray.Dataset`,
  `xarray.DataTree`, `ppfive.File`, `netCDF4.Dataset`,
  `scipy.io.netcdf_file`, and `h5py.File`.

- Any object ``x`` that accesses the dataset and has the same API as
  one of the allowed backend objects. In pratice, this means any
  object ``x`` for which ``isinstance(x, <backend-object>)`` is `True`
  for any ``<backend-object>`` from the selection of allowed backend
  objects.

### A simple example
    
An example of how to use `xnetcdf` to open a dataset and inspect its
contents:

```python
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

```
The dataset is presented in terms of netCDF groups, dimensions and
variables (there is only the root group in this example), which can
contain attributes and data arrays.

See the
[documentation](https://xnetcdf.readthedocs.io/en/latest/quickstart/)
for more information and examples.

## Dependencies

`xnetcdf` is tested against Python versions 3.10 to 3.14.  It may
also work with other Python versions.

The only dependency required run the software, besides Python, is
`numpy`.

However, each of the backend libraries `pyfive`, `netCDF4`, `zarr`,
`scipy.io.netcdf_file`, `xarray`, `ppfive`, and `h5py` can only be
used if it also installed. It is not a problem, in general, if a
backend library is not installed, as it just reduces the size of the
pool of backends that are available for reading a dataset.

## Installation

xnetcdf can be installed using `pip` using the command:

``` shell
$ pip install xnetcdf
```

or, to also install all of the backend libraries:

``` shell
$ pip install xnetcdf[all]
```

`conda` packages, which also install all of the backend libraries, are
also available from conda-forge:

``` shell
$ conda install -c conda-forge xnetcdf
```
To install from source in your home directory use:

``` shell
$ pip install --user ./xnetcdf
```
The library can also be imported directly from the `xnetcdf` source
root directory:

``` shell
$ pip install -e . 
```

### Conda-forge feedstock

Package repository [conda-forge
feedstock](https://github.com/conda-forge/xnetcdf-feedstock).

## Contributing

See the [Contributing
page](https://xnetcdf.readthedocs.io/en/latest/contributing/) of the
documentation for details.

## Development

### Testing

Run the `pytest` test suite:

``` shell
$ cd xnetcdf
$ pytest
```

### Documentation

Build the documentation with `sphinx`:

``` console
$ cd xnetcdf/docs
$ make html
```
	
View the documentation locally at `xnetcdf/docs/build/html/index.html`.
