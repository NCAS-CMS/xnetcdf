from pathlib import Path

import numpy as np
import pytest


@pytest.fixture(scope="session")
def data_dir():
    """Returns the absolute Path to the tests/data directory."""
    # __file__ is the path to conftest.py, .parent is the tests/ directory
    return Path(__file__).parent / "data"


@pytest.fixture
def generate_netCDF4_file(data_dir):
    """Create the netCDF-4 test file."""
    import netCDF4

    ncfile = data_dir / "test.nc"

    # ------------------------------------------------------------
    # NETCDF4
    # ------------------------------------------------------------
    with netCDF4.Dataset(ncfile, "w", format="NETCDF4") as nc:
        # Global Attributes
        nc.setncattr("Conventions", "CF-1.13")
        nc.setncattr("global_attr_1", 3.14)
        nc.setncattr("global_attr_2", "foo")

        # Dimensions for root group
        nc.createDimension("bounds2", 2)

        # Root group variables
        time = nc.createVariable("time", "i4")
        time.setncattr("units", "days since 2018-12-01")
        time.setncattr("standard_name", "time")
        time[...] = 31

        # Group: forecast
        forecast = nc.createGroup("forecast")
        forecast.createDimension("lon", None)  # UNLIMITED

        lon_bnds = forecast.createVariable(
            "lon_bnds", "f8", ("lon", "bounds2")
        )

        lon = forecast.createVariable("lon", "f8", ("lon",))
        lon.setncattr("units", "degrees_east")
        lon.setncattr("standard_name", "longitude")
        lon.setncattr("bounds", "/forecast/lon_bnds")

        # Data for forecast group
        lon[...] = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]
        lon_bnds[...] = [
            [0, 45],
            [45, 90],
            [90, 135],
            [135, 180],
            [180, 225],
            [225, 270],
            [270, 315],
            [315, 360],
        ]

        # Group: forecast/model
        model = forecast.createGroup("model")
        model.createDimension("lat", 5)

        # Group attributes
        model.setncattr("group_attr_1", np.int64(12))
        model.setncattr("group_attr_2", "bar")

        lat_bnds = model.createVariable("lat_bnds", "f8", ("lat", "bounds2"))

        lat = model.createVariable("lat", "f8", ("lat",), contiguous=True)
        lat.setncattr("units", "degrees_north")
        lat.setncattr("standard_name", "latitude")
        lat.setncattr("bounds", "/forecast/model/lat_bnds")

        # The 'q' variable (uses 'lon' from the parent group and 'lat'
        # from current group)
        q = model.createVariable("q", "f4", ("lat", "lon"), chunksizes=(5, 3))

        # int and float attributes for 'q'
        q.setncattr("int", 49)
        q.setncattr("int8", np.int8(49))
        q.setncattr("int16", np.int16(49))
        q.setncattr("int32", np.int32(49))
        q.setncattr("int64", np.int64(49))
        q.setncattr("float", 49.0)
        q.setncattr("float32", np.float32(49.0))
        q.setncattr("float64", np.float64(49.0))
        q.setncattr("uint8", np.uint8(49))
        q.setncattr("uint16", np.uint16(49))
        q.setncattr("uint32", np.uint32(49))
        q.setncattr("uint64", np.uint64(49))

        # list attributes
        q.setncattr("list1", np.array([2, 3], dtype="int8"))
        q.setncattr("list2", np.array([2, 3], dtype="int16"))
        q.setncattr("list3", np.array([2, 3], dtype="int64"))
        q.setncattr("list4", np.array([2, 3], dtype="int32"))
        q.setncattr("list5", np.array([2.0, 3.0], dtype="float32"))
        q.setncattr("list6", np.array([2.0, 3.0], dtype="float64"))
        q.setncattr("list7", [2, 3])
        q.setncattr("list8", np.array([2], dtype="int32"))
        q.setncattr("list9", np.array([], dtype="int32"))
        q.setncattr("list10", [])
        q.setncattr("list11", ["a", "bb", "ccc"])
        q.setncattr("list12", ["a", "1", "2.5"])
        q.setncattr("list13", np.array(["a"], dtype="U"))
        q.setncattr("list14", np.array(["a", "bb"], dtype="U"))

        # char attributes
        q.setncattr("string1", "1")
        q.setncattr("string2", "a")
        q.setncattr("string3", "kg m-2")
        q.setncattr("string4", "")
        q.setncattr("string5", " ")
        q.setncattr("string6", b"")
        q.setncattr("string7", np.bytes_(""))
        q.setncattr("string8", np.bytes_([]))
        q.setncattr("string9", np.array([], dtype="S1"))

        # Coordinates and methods
        q.setncattr("coordinates", "time")
        q.setncattr("cell_methods", "area: mean")

        q.setncattr("standard_name", "specific_humidity")

        # Data for model group
        lat[...] = [-75, -45, 0, 45, 75]
        lat_bnds[...] = [
            [-90, -60],
            [-60, -30],
            [-30, 30],
            [30, 60],
            [60, 90],
        ]

        q[...] = [
            [0.007, 0.034, 0.003, 0.014, 0.018, 0.037, 0.024, 0.029],
            [0.023, 0.036, 0.045, 0.062, 0.046, 0.073, 0.006, 0.066],
            [0.11, 0.131, 0.124, 0.146, 0.087, 0.103, 0.057, 0.011],
            [0.029, 0.059, 0.039, 0.07, 0.058, 0.072, 0.009, 0.017],
            [0.006, 0.036, 0.019, 0.035, 0.018, 0.037, 0.034, 0.013],
        ]

    yield ncfile
