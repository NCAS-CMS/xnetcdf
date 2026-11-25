from pathlib import Path

import numpy as np
import pytest
import xarray as xr

import xnetcdf
from xnetcdf.utils import xarray_undecode_cf


def test_netCDF4_1(data_dir):
    """Test netCDF4 functionality."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="netCDF4") as p:
        assert p.backend_api == "netCDF4"
        assert (
            p.dump(display=False)
            == f"""{p.dataset_name}: <xnetcdf.Dataset: /, 1 dimension, 1 variable, 1 group>
    Attributes:
        Conventions: 'CF-1.13'
        global_attr_1: np.float64(3.14)
        global_attr_2: 'foo'
    Dimensions:
        bounds2: <xnetcdf.Dimension: /bounds2, size=2>
    Variables:
        time: <xnetcdf.Variable: /time, shape=(), dimensions=()>
            Attributes:
                standard_name: 'time'
                units: 'days since 2018-12-01'
    Groups:
        forecast: <xnetcdf.Group: /forecast, 1 dimension, 2 variables, 1 group>
            Dimensions:
                lon: <xnetcdf.Dimension: /forecast/lon, size=8, unlimited>
            Variables:
                lon_bnds: <xnetcdf.Variable: /forecast/lon_bnds, shape=(8, 2), dimensions=(/forecast/lon, /bounds2)>
                lon: <xnetcdf.Variable: /forecast/lon, shape=(8,), dimensions=(/forecast/lon,)>
                    Attributes:
                        bounds: '/forecast/lon_bnds'
                        standard_name: 'longitude'
                        units: 'degrees_east'
            Groups:
                model: <xnetcdf.Group: /forecast/model, 1 dimension, 3 variables, 0 groups>
                    Attributes:
                        group_attr_1: np.int64(12)
                        group_attr_2: 'bar'
                    Dimensions:
                        lat: <xnetcdf.Dimension: /forecast/model/lat, size=5>
                    Variables:
                        lat_bnds: <xnetcdf.Variable: /forecast/model/lat_bnds, shape=(5, 2), dimensions=(/forecast/model/lat, /bounds2)>
                        lat: <xnetcdf.Variable: /forecast/model/lat, shape=(5,), dimensions=(/forecast/model/lat,)>
                            Attributes:
                                bounds: '/forecast/model/lat_bnds'
                                standard_name: 'latitude'
                                units: 'degrees_north'
                        q: <xnetcdf.Variable: /forecast/model/q, shape=(5, 8), dimensions=(/forecast/model/lat, /forecast/lon)>
                            Attributes:
                                cell_methods: 'area: mean'
                                coordinates: 'time'
                                float: np.float64(49.0)
                                float32: np.float32(49.0)
                                float64: np.float64(49.0)
                                int: np.int64(49)
                                int16: np.int16(49)
                                int32: np.int32(49)
                                int64: np.int64(49)
                                int8: np.int8(49)
                                list1: array([2, 3], dtype=int8)
                                list10: array([], dtype=float64)
                                list11: ['a', 'bb', 'ccc']
                                list12: ['a', '1', '2.5']
                                list13: 'a'
                                list14: ['a', 'bb']
                                list2: array([2, 3], dtype=int16)
                                list3: array([2, 3])
                                list4: array([2, 3], dtype=int32)
                                list5: array([2., 3.], dtype=float32)
                                list6: array([2., 3.])
                                list7: array([2, 3])
                                list8: np.int32(2)
                                list9: array([], dtype=int32)
                                standard_name: 'specific_humidity'
                                string1: '1'
                                string2: 'a'
                                string3: 'kg m-2'
                                string4: ''
                                string5: ' '
                                string6: ''
                                string7: ''
                                string8: ''
                                string9: ''
                                uint16: np.uint16(49)
                                uint32: np.uint32(49)
                                uint64: np.uint64(49)
                                uint8: np.uint8(49)"""
        )


def test_netCDF4_2(data_dir):
    """Test netCDF4 functionality."""
    import netCDF4

    dataset = data_dir / "test.nc"
    with netCDF4.Dataset(str(dataset)) as x:
        with (
            xnetcdf.Dataset(dataset, backend="netCDF4") as p1,
            xnetcdf.Dataset(x, backend="netCDF4") as p2,
        ):
            assert p1.backend_api == "netCDF4"
            assert p2.backend_api == "netCDF4"
            assert p1.dump(display=False, data=True) == p2.dump(
                display=False, data=True
            )


def test_zarr3_1(data_dir):
    """Test Zarr3 functionality."""
    dataset = data_dir / "test.zarr3"
    with xnetcdf.Dataset(dataset) as p:
        assert p.backend_api == "zarr"
        assert (
            p.dump(display=False)
            == f"""{p.dataset_name}: <xnetcdf.Dataset: /, 0 dimensions, 1 variable, 1 group>
    Attributes:
        Conventions: 'CF-1.13'
        global_attr_1: 3.14
        global_attr_2: 'foo'
    Variables:
        time: <xnetcdf.Variable: /time, shape=(), dimensions=()>
            Attributes:
                standard_name: 'time'
                units: 'days since 2018-12-01'
    Groups:
        forecast: <xnetcdf.Group: /forecast, 2 dimensions, 2 variables, 1 group>
            Dimensions:
                lon: <xnetcdf.Dimension: /forecast/lon, size=8>
                bounds2: <xnetcdf.Dimension: /forecast/bounds2, size=2>
            Variables:
                lon: <xnetcdf.Variable: /forecast/lon, shape=(8,), dimensions=(/forecast/lon,)>
                    Attributes:
                        bounds: '/forecast/lon_bnds'
                        standard_name: 'longitude'
                        units: 'degrees_east'
                lon_bnds: <xnetcdf.Variable: /forecast/lon_bnds, shape=(8, 2), dimensions=(/forecast/lon, /forecast/bounds2)>
            Groups:
                model: <xnetcdf.Group: /forecast/model, 1 dimension, 3 variables, 0 groups>
                    Attributes:
                        group_attr_1: 12
                        group_attr_2: 'bar'
                    Dimensions:
                        lat: <xnetcdf.Dimension: /forecast/model/lat, size=5>
                    Variables:
                        lat: <xnetcdf.Variable: /forecast/model/lat, shape=(5,), dimensions=(/forecast/model/lat,)>
                            Attributes:
                                bounds: '/forecast/model/lat_bnds'
                                standard_name: 'latitude'
                                units: 'degrees_north'
                        lat_bnds: <xnetcdf.Variable: /forecast/model/lat_bnds, shape=(5, 2), dimensions=(/forecast/model/lat, /forecast/bounds2)>
                        q: <xnetcdf.Variable: /forecast/model/q, shape=(5, 8), dimensions=(/forecast/model/lat, /forecast/lon)>
                            Attributes:
                                cell_methods: 'area: mean'
                                coordinates: 'time'
                                float: 49.0
                                float32: 49.0
                                float64: 49.0
                                int: 49
                                int16: 49
                                int32: 49
                                int64: 49
                                int8: 49
                                list1: array([2, 3])
                                list10: []
                                list11: ['a', 'bb', 'ccc']
                                list12: ['a', '1', '2.5']
                                list13: 'a'
                                list14: ['a', 'bb']
                                list2: array([2, 3])
                                list3: array([2, 3])
                                list4: array([2, 3])
                                list5: array([2., 3.])
                                list6: array([2., 3.])
                                list7: array([2, 3])
                                list8: 2
                                list9: []
                                standard_name: 'specific_humidity'
                                string1: '1'
                                string2: 'a'
                                string3: 'kg m-2'
                                string4: ''
                                string5: ' '
                                string6: ''
                                string7: ''
                                string8: ''
                                string9: ''
                                uint16: 49
                                uint32: 49
                                uint64: 49
                                uint8: 49"""
        )


def test_zarr3_2(data_dir):
    """Test zarr3 functionality."""
    import zarr

    dataset = data_dir / "test.zarr3"
    x = zarr.open(dataset)
    with (
        xnetcdf.Dataset(dataset, backend="zarr") as p1,
        xnetcdf.Dataset(x, backend="zarr") as p2,
    ):
        assert p1.backend_api == "zarr"
        assert p2.backend_api == "zarr"
        assert p1.dump(display=False, data=True) == p2.dump(display=False, data=True)


def test_zarr2_1(data_dir):
    """Test Zarr2 functionality."""
    dataset = data_dir / "test1.zarr2"
    with xnetcdf.Dataset(dataset) as p:
        assert p.backend_api == "zarr"
        assert (
            p.dump(display=False)
            == f"""{p.dataset_name}: <xnetcdf.Dataset: /, 3 dimensions, 6 variables, 0 groups>
    Attributes:
        Conventions: 'CF-1.12'
    Dimensions:
        lat: <xnetcdf.Dimension: /lat, size=5>
        bounds2: <xnetcdf.Dimension: /bounds2, size=2>
        lon: <xnetcdf.Dimension: /lon, size=8>
    Variables:
        lat: <xnetcdf.Variable: /lat, shape=(5,), dimensions=(/lat,)>
            Attributes:
                bounds: 'lat_bnds'
                standard_name: 'latitude'
                units: 'degrees_north'
        lat_bnds: <xnetcdf.Variable: /lat_bnds, shape=(5, 2), dimensions=(/lat, /bounds2)>
        lon: <xnetcdf.Variable: /lon, shape=(8,), dimensions=(/lon,)>
            Attributes:
                bounds: 'lon_bnds'
                standard_name: 'longitude'
                units: 'degrees_east'
        lon_bnds: <xnetcdf.Variable: /lon_bnds, shape=(8, 2), dimensions=(/lon, /bounds2)>
        q: <xnetcdf.Variable: /q, shape=(5, 8), dimensions=(/lat, /lon)>
            Attributes:
                cell_methods: 'area: mean'
                coordinates: 'time'
                project: 'research'
                standard_name: 'specific_humidity'
                units: '1'
        time: <xnetcdf.Variable: /time, shape=(), dimensions=()>
            Attributes:
                standard_name: 'time'
                units: 'days since 2018-12-01'"""
        )


def test_zarr2_2(data_dir):
    """Test zarr2 functionality."""
    import zarr

    dataset = data_dir / "test.zarr2"
    z = zarr.open(dataset)
    with (
        xnetcdf.Dataset(dataset, backend="zarr") as p1,
        xnetcdf.Dataset(z, backend="zarr") as p2,
    ):
        assert p1.backend_api == "zarr"
        assert p2.backend_api == "zarr"
        assert p1.dump(display=False, data=True) == p2.dump(display=False, data=True)


def test_kerchunk(data_dir):
    """Test Kerchunk functionality."""
    import fsspec

    dataset = str(data_dir / "test1.kerchunk")
    mapper = fsspec.filesystem("reference", fo=dataset).get_mapper()
    with xnetcdf.Dataset(mapper) as p:
        assert p.backend_api == "zarr"
        assert (
            p.dump(display=False)
            == f"""{p.dataset_name}: <xnetcdf.Dataset: /, 3 dimensions, 6 variables, 0 groups>
    Attributes:
        Conventions: 'CF-1.12'
    Dimensions:
        lat: <xnetcdf.Dimension: /lat, size=5>
        bounds2: <xnetcdf.Dimension: /bounds2, size=2>
        lon: <xnetcdf.Dimension: /lon, size=8>
    Variables:
        lat: <xnetcdf.Variable: /lat, shape=(5,), dimensions=(/lat,)>
            Attributes:
                bounds: 'lat_bnds'
                standard_name: 'latitude'
                units: 'degrees_north'
        lat_bnds: <xnetcdf.Variable: /lat_bnds, shape=(5, 2), dimensions=(/lat, /bounds2)>
        lon: <xnetcdf.Variable: /lon, shape=(8,), dimensions=(/lon,)>
            Attributes:
                bounds: 'lon_bnds'
                standard_name: 'longitude'
                units: 'degrees_east'
        lon_bnds: <xnetcdf.Variable: /lon_bnds, shape=(8, 2), dimensions=(/lon, /bounds2)>
        q: <xnetcdf.Variable: /q, shape=(5, 8), dimensions=(/lat, /lon)>
            Attributes:
                cell_methods: 'area: mean'
                coordinates: 'time'
                project: 'research'
                standard_name: 'specific_humidity'
                units: '1'
        time: <xnetcdf.Variable: /time, shape=(), dimensions=()>
            Attributes:
                standard_name: 'time'
                units: 'days since 2018-12-01'"""
        )


def test_netcdf_file_1(data_dir):
    """Test Kerchunk functionality."""
    dataset = data_dir / "test1.nc3"
    with xnetcdf.Dataset(dataset, backend="netcdf_file") as p:
        assert p.backend_api == "netcdf_file"
        assert (
            p.dump(display=False)
            == f"""{p.dataset_name}: <xnetcdf.Dataset: /, 3 dimensions, 6 variables, 0 groups>
    Attributes:
        Conventions: 'CF-1.13'
    Dimensions:
        lat: <xnetcdf.Dimension: /lat, size=5>
        bounds2: <xnetcdf.Dimension: /bounds2, size=2>
        lon: <xnetcdf.Dimension: /lon, size=8>
    Variables:
        lat_bnds: <xnetcdf.Variable: /lat_bnds, shape=(5, 2), dimensions=(/lat, /bounds2)>
        lat: <xnetcdf.Variable: /lat, shape=(5,), dimensions=(/lat,)>
            Attributes:
                bounds: 'lat_bnds'
                standard_name: 'latitude'
                units: 'degrees_north'
        lon_bnds: <xnetcdf.Variable: /lon_bnds, shape=(8, 2), dimensions=(/lon, /bounds2)>
        lon: <xnetcdf.Variable: /lon, shape=(8,), dimensions=(/lon,)>
            Attributes:
                bounds: 'lon_bnds'
                standard_name: 'longitude'
                units: 'degrees_east'
        time: <xnetcdf.Variable: /time, shape=(), dimensions=()>
            Attributes:
                standard_name: 'time'
                units: 'days since 2018-12-01'
        q: <xnetcdf.Variable: /q, shape=(5, 8), dimensions=(/lat, /lon)>
            Attributes:
                cell_methods: 'area: mean'
                coordinates: 'time'
                project: 'research'
                standard_name: 'specific_humidity'
                units: '1'"""
        )


def test_netcdf_file_2(data_dir):
    """Test netcdf_file functionality."""
    from scipy.io import netcdf_file

    dataset = data_dir / "test1.nc3"
    x = netcdf_file(dataset)
    with (
        xnetcdf.Dataset(dataset, backend="netcdf_file") as p1,
        xnetcdf.Dataset(x, backend="netcdf_file") as p2,
    ):
        assert p1.backend_api == "netcdf_file"
        assert p2.backend_api == "netcdf_file"
        assert p1.dump(display=False, data=True) == p2.dump(display=False, data=True)

    x._mm_buf = None
    x.close()


def test_umfive_1(data_dir):
    """Test umfive functionality."""
    dataset = data_dir / "extra_data.pp"
    with xnetcdf.Dataset(dataset, backend="umfive") as p:
        assert p.backend_api == "umfive"
        assert (
            p.dump(display=False)
            == f"""{p.dataset_name}: <xnetcdf.Dataset: /, 5 dimensions, 9 variables, 0 groups>
    Attributes:
        Conventions: 'CF-1.13'
    Dimensions:
        height: <xnetcdf.Dimension: /height, size=1>
        time: <xnetcdf.Dimension: /time, size=100>
        site: <xnetcdf.Dimension: /site, size=3>
        bounds2: <xnetcdf.Dimension: /bounds2, size=2>
        dimension1: <xnetcdf.Dimension: /dimension1, size=1>
    Variables:
        UM_m01s03i236_vn405: <xnetcdf.Variable: /UM_m01s03i236_vn405, shape=(1, 1, 100, 3), dimensions=(/dimension1, /height, /time, /site)>
            Attributes:
                _FillValue: np.float32(-1.0737418e+09)
                cell_methods: 'realization: mean time: mean'
                coordinates: 'height time site longitude latitude region'
                lbcode: '11323'
                lbpack: '0'
                lbproc: '131200'
                lbtim: '22'
                lbvc: '1'
                long_name: 'TEMPERATURE AT 1.5M'
                missing_value: np.float32(-1.0737418e+09)
                runid: 'xfqqp'
                source: 'UM'
                standard_name: 'air_temperature'
                stash_code: '3236'
                submodel: '1'
                um_identity: 'UM_m01s03i236_vn405'
                um_stash_source: 'm01s03i236'
                um_version: '4.5'
                units: 'K'
        height: <xnetcdf.Variable: /height, shape=(1,), dimensions=(/height,)>
            Attributes:
                axis: 'Z'
                positive: 'up'
                standard_name: 'height'
                units: 'm'
        time: <xnetcdf.Variable: /time, shape=(100,), dimensions=(/time,)>
            Attributes:
                axis: 'T'
                calendar: '360_day'
                standard_name: 'time'
                units: 'days since 0-1-1'
        site: <xnetcdf.Variable: /site, shape=(3,), dimensions=(/site,)>
            Attributes:
                long_name: 'site'
        longitude: <xnetcdf.Variable: /longitude, shape=(3,), dimensions=(/site,)>
            Attributes:
                bounds: 'longitude_bounds'
                long_name: 'region limit'
                standard_name: 'longitude'
                units: 'degrees_east'
        longitude_bounds: <xnetcdf.Variable: /longitude_bounds, shape=(3, 2), dimensions=(/site, /bounds2)>
        latitude: <xnetcdf.Variable: /latitude, shape=(3,), dimensions=(/site,)>
            Attributes:
                bounds: 'latitude_bounds'
                long_name: 'region limit'
                standard_name: 'latitude'
                units: 'degrees_north'
        latitude_bounds: <xnetcdf.Variable: /latitude_bounds, shape=(3, 2), dimensions=(/site, /bounds2)>
        region: <xnetcdf.Variable: /region, shape=(3,), dimensions=(/site,)>
            Attributes:
                standard_name: 'region'"""
        )


def test_umfive_2(data_dir):
    """Test umfive functionality."""
    import umfive

    dataset = data_dir / "extra_data.pp"
    with umfive.File(dataset) as x:
        with (
            xnetcdf.Dataset(dataset, backend="umfive") as p1,
            xnetcdf.Dataset(x, backend="umfive") as p2,
        ):
            assert p1.backend_api == "umfive"
            assert p2.backend_api == "umfive"
            assert p1.dump(display=False, data=True) == p2.dump(
                display=False, data=True
            )


def test_xarray_1(data_dir):
    """Test xarray functionality."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="xarray") as p:
        assert p.backend_api == "xarray"
        assert (
            p.dump(display=False)
            == f"""{p.dataset_name}: <xnetcdf.Dataset: /, 0 dimensions, 1 variable, 1 group>
    Attributes:
        Conventions: 'CF-1.13'
        global_attr_1: np.float64(3.14)
        global_attr_2: 'foo'
    Variables:
        time: <xnetcdf.Variable: /time, shape=(), dimensions=()>
            Attributes:
                standard_name: 'time'
                units: 'days since 2018-12-01'
    Groups:
        forecast: <xnetcdf.Group: /forecast, 2 dimensions, 2 variables, 1 group>
            Dimensions:
                lon: <xnetcdf.Dimension: /forecast/lon, size=8, unlimited>
                bounds2: <xnetcdf.Dimension: /forecast/bounds2, size=2>
            Variables:
                lon_bnds: <xnetcdf.Variable: /forecast/lon_bnds, shape=(8, 2), dimensions=(/forecast/lon, /forecast/bounds2)>
                lon: <xnetcdf.Variable: /forecast/lon, shape=(8,), dimensions=(/forecast/lon,)>
                    Attributes:
                        bounds: '/forecast/lon_bnds'
                        standard_name: 'longitude'
                        units: 'degrees_east'
            Groups:
                model: <xnetcdf.Group: /forecast/model, 1 dimension, 3 variables, 0 groups>
                    Attributes:
                        group_attr_1: np.int64(12)
                        group_attr_2: 'bar'
                    Dimensions:
                        lat: <xnetcdf.Dimension: /forecast/model/lat, size=5>
                    Variables:
                        lat_bnds: <xnetcdf.Variable: /forecast/model/lat_bnds, shape=(5, 2), dimensions=(/forecast/model/lat, /forecast/bounds2)>
                        q: <xnetcdf.Variable: /forecast/model/q, shape=(5, 8), dimensions=(/forecast/model/lat, /forecast/lon)>
                            Attributes:
                                cell_methods: 'area: mean'
                                coordinates: 'time'
                                float: np.float64(49.0)
                                float32: np.float32(49.0)
                                float64: np.float64(49.0)
                                int: np.int64(49)
                                int16: np.int16(49)
                                int32: np.int32(49)
                                int64: np.int64(49)
                                int8: np.int8(49)
                                list1: array([2, 3], dtype=int8)
                                list10: array([], dtype=float64)
                                list11: ['a', 'bb', 'ccc']
                                list12: ['a', '1', '2.5']
                                list13: 'a'
                                list14: ['a', 'bb']
                                list2: array([2, 3], dtype=int16)
                                list3: array([2, 3])
                                list4: array([2, 3], dtype=int32)
                                list5: array([2., 3.], dtype=float32)
                                list6: array([2., 3.])
                                list7: array([2, 3])
                                list8: np.int32(2)
                                list9: array([], dtype=int32)
                                standard_name: 'specific_humidity'
                                string1: '1'
                                string2: 'a'
                                string3: 'kg m-2'
                                string4: ''
                                string5: ' '
                                string6: ''
                                string7: ''
                                string8: ''
                                string9: ''
                                uint16: np.uint16(49)
                                uint32: np.uint32(49)
                                uint64: np.uint64(49)
                                uint8: np.uint8(49)
                        lat: <xnetcdf.Variable: /forecast/model/lat, shape=(5,), dimensions=(/forecast/model/lat,)>
                            Attributes:
                                bounds: '/forecast/model/lat_bnds'
                                standard_name: 'latitude'
                                units: 'degrees_north'"""
        )


def test_xarray_2(data_dir):
    """Test xarray functionality."""
    import xarray

    dataset = data_dir / "test.nc"
    with xarray.open_datatree(dataset, mask_and_scale=False, decode_cf=False) as x:
        with (
            xnetcdf.Dataset(dataset, backend="xarray") as p1,
            xnetcdf.Dataset(x, backend="xarray") as p2,
        ):
            assert p1.backend_api == "xarray"
            assert p2.backend_api == "xarray"
            assert p1.dump(display=False, data=True) == p2.dump(
                display=False, data=True
            )


def test_h5py_1(data_dir):
    """Test h5py functionality."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="h5py") as p:
        assert p.backend_api == "h5py"
        assert (
            p.dump(display=False)
            == f"""{p.dataset_name}: <xnetcdf.Dataset: /, 1 dimension, 1 variable, 1 group>
    Attributes:
        Conventions: 'CF-1.13'
        global_attr_1: np.float64(3.14)
        global_attr_2: 'foo'
    Dimensions:
        bounds2: <xnetcdf.Dimension: /bounds2, size=2>
    Variables:
        time: <xnetcdf.Variable: /time, shape=(), dimensions=()>
            Attributes:
                standard_name: 'time'
                units: 'days since 2018-12-01'
    Groups:
        forecast: <xnetcdf.Group: /forecast, 1 dimension, 2 variables, 1 group>
            Dimensions:
                lon: <xnetcdf.Dimension: /forecast/lon, size=8, unlimited>
            Variables:
                lon_bnds: <xnetcdf.Variable: /forecast/lon_bnds, shape=(8, 2), dimensions=(/forecast/lon, /bounds2)>
                lon: <xnetcdf.Variable: /forecast/lon, shape=(8,), dimensions=(/forecast/lon,)>
                    Attributes:
                        bounds: '/forecast/lon_bnds'
                        standard_name: 'longitude'
                        units: 'degrees_east'
            Groups:
                model: <xnetcdf.Group: /forecast/model, 1 dimension, 3 variables, 0 groups>
                    Attributes:
                        group_attr_1: np.int64(12)
                        group_attr_2: 'bar'
                    Dimensions:
                        lat: <xnetcdf.Dimension: /forecast/model/lat, size=5>
                    Variables:
                        lat_bnds: <xnetcdf.Variable: /forecast/model/lat_bnds, shape=(5, 2), dimensions=(/forecast/model/lat, /bounds2)>
                        lat: <xnetcdf.Variable: /forecast/model/lat, shape=(5,), dimensions=(/forecast/model/lat,)>
                            Attributes:
                                bounds: '/forecast/model/lat_bnds'
                                standard_name: 'latitude'
                                units: 'degrees_north'
                        q: <xnetcdf.Variable: /forecast/model/q, shape=(5, 8), dimensions=(/forecast/model/lat, /forecast/lon)>
                            Attributes:
                                cell_methods: 'area: mean'
                                coordinates: 'time'
                                float: np.float64(49.0)
                                float32: np.float32(49.0)
                                float64: np.float64(49.0)
                                int: np.int64(49)
                                int16: np.int16(49)
                                int32: np.int32(49)
                                int64: np.int64(49)
                                int8: np.int8(49)
                                list1: array([2, 3], dtype=int8)
                                list10: array([], dtype=float64)
                                list11: ['a', 'bb', 'ccc']
                                list12: ['a', '1', '2.5']
                                list13: 'a'
                                list14: ['a', 'bb']
                                list2: array([2, 3], dtype=int16)
                                list3: array([2, 3])
                                list4: array([2, 3], dtype=int32)
                                list5: array([2., 3.], dtype=float32)
                                list6: array([2., 3.])
                                list7: array([2, 3])
                                list8: np.int32(2)
                                list9: array([], dtype=int32)
                                standard_name: 'specific_humidity'
                                string1: '1'
                                string2: 'a'
                                string3: 'kg m-2'
                                string4: ''
                                string5: ' '
                                string6: ''
                                string7: ''
                                string8: ''
                                string9: ''
                                uint16: np.uint16(49)
                                uint32: np.uint32(49)
                                uint64: np.uint64(49)
                                uint8: np.uint8(49)"""
        )


def test_h5py_2(data_dir):
    """Test h5py functionality."""
    import h5py

    dataset = data_dir / "test.nc"
    with h5py.File(dataset) as x:
        with (
            xnetcdf.Dataset(dataset, backend="h5py") as p1,
            xnetcdf.Dataset(x, backend="h5py") as p2,
        ):
            assert p1.backend_api == "h5py"
            assert p2.backend_api == "h5py"
            assert p1.dump(display=False, data=True) == p2.dump(
                display=False, data=True
            )


def test_pyfive_2(data_dir):
    """Test pyfive functionality."""
    import pyfive

    dataset = data_dir / "test.nc"
    with pyfive.File(dataset) as x:
        with (
            xnetcdf.Dataset(dataset, backend="pyfive") as p1,
            xnetcdf.Dataset(x, backend="pyfive") as p2,
        ):
            assert p1.backend_api == "pyfive"
            assert p2.backend_api == "pyfive"
            assert p1.dump(display=False, data=True) == p2.dump(
                display=False, data=True
            )


def _assert_datasets_match_raw(actual: xr.Dataset, expected: xr.Dataset):
    """Assert unencoded Datasets match."""
    assert set(actual.data_vars) == set(expected.data_vars)
    assert set(actual.coords) == set(expected.coords)
    assert actual.attrs == expected.attrs
    assert actual.encoding.get("unlimited_dims", set()) == (
        expected.encoding.get("unlimited_dims", set())
    )

    for name in expected.variables:
        act_var = actual[name]
        exp_var = expected[name]

        assert act_var.dims == exp_var.dims
        assert act_var.dtype == exp_var.dtype
        np.testing.assert_equal(act_var.values, exp_var.values)

        act_attrs = dict(act_var.attrs)
        exp_attrs = dict(exp_var.attrs)
        # Xarray infers 'proleptic_gregorian' on decode when 'calendar' is
        # omitted on disk, so cf_encoder writes it back on re-encode.
        if (
            "calendar" not in exp_attrs
            and act_attrs.get("calendar") == "proleptic_gregorian"
        ):
            act_attrs.pop("calendar")

        assert act_attrs.keys() == exp_attrs.keys()
        for attr, exp_val in exp_attrs.items():
            np.testing.assert_equal(act_attrs[attr], exp_val)


@pytest.mark.parametrize("group", [None, "/forecast", "/forecast/model"])
def test_xarray_undecode_cf_dataset_groups(data_dir, group):
    """Check group.

    xarray_undecode_cf(decode_cf=True) matches
    open_dataset(decode_cf=False).

    """
    test_nc_path = data_dir / "test.nc"
    raw = xr.open_dataset(test_nc_path, group=group, decode_cf=False)
    decoded = xr.open_dataset(test_nc_path, group=group, decode_cf=True)

    # Snapshot input to verify xarray_undecode_cf does not mutate it
    orig_vars = set(decoded.variables)
    orig_coords = set(decoded.coords)

    reverted = xarray_undecode_cf(decoded)

    assert set(decoded.variables) == orig_vars
    assert set(decoded.coords) == orig_coords
    _assert_datasets_match_raw(reverted, raw)

    # Idempotency: unencoding an already-raw Dataset is a no-op
    _assert_datasets_match_raw(xarray_undecode_cf(raw), raw)


def test_xarray_undecode_cf_datatree(data_dir):
    """Check DataTree.

    xarray_undecode_cf on a DataTree reproduces
    open_datatree(decode_cf=False).

    """
    test_nc_path = data_dir / "test.nc"
    raw_dt = xr.open_datatree(test_nc_path, decode_cf=False)
    decoded_dt = xr.open_datatree(test_nc_path, decode_cf=True)

    reverted_dt = xarray_undecode_cf(decoded_dt)

    assert [n.path for n in reverted_dt.subtree] == [n.path for n in raw_dt.subtree]

    for raw_node, rev_node in zip(raw_dt.subtree, reverted_dt.subtree):
        raw_ds = raw_node.to_dataset(inherit=False)
        rev_ds = rev_node.to_dataset(inherit=False)
        _assert_datasets_match_raw(rev_ds, raw_ds)

    # Spot-check key features from the test file
    root = reverted_dt["/"].to_dataset(inherit=False)
    assert "time" in root.data_vars
    assert "time" not in root.coords
    assert root["time"].attrs["units"] == "days since 2018-12-01"
    assert "_FillValue" not in root["time"].attrs

    model = reverted_dt["/forecast/model"].to_dataset(inherit=False)
    assert model.attrs["group_attr_2"] == "bar"
    assert model["q"].attrs["standard_name"] == "specific_humidity"
    assert model["q"].attrs["coordinates"] == "time"
    assert "coordinates" not in model["lat_bnds"].attrs
    assert "_FillValue" not in model["lat_bnds"].attrs


def test_unencode_cf_packing_masking_and_bounds(tmp_path: Path):
    """Check _FillValue, scale/offset, unlimited_dims, and bounds."""
    nc_path = tmp_path / "cf_features.nc"

    # Build a raw CF dataset directly so disk metadata is exact
    ds_disk = xr.Dataset(
        data_vars={
            "time": xr.Variable(
                ("time",),
                np.array([0.0, 1.0], dtype="float64"),
                attrs={
                    "units": "days since 2020-01-01",
                    "calendar": "standard",
                },
            ),
            "lon_bnds": xr.Variable(
                ("lon", "bnds"),
                np.array([[0.0, 10.0], [10.0, 20.0]], dtype="float64"),
                attrs={"units": "degrees_east"},
            ),
            "tas": xr.Variable(
                ("time", "lon"),
                np.array([[100, -999], [200, 300]], dtype="int16"),
                attrs={
                    "units": "K",
                    "scale_factor": np.float32(0.1),
                    "add_offset": np.float32(250.0),
                    "_FillValue": np.int16(-999),
                    "coordinates": "time",
                },
            ),
        },
        coords={
            "lon": xr.Variable(
                ("lon",),
                np.array([5.0, 15.0], dtype="float64"),
                attrs={"units": "degrees_east", "bounds": "lon_bnds"},
            ),
        },
    )

    ds_disk.encoding["unlimited_dims"] = {"time"}
    ds_disk.to_netcdf(nc_path, mode="w", format="NETCDF4")

    # Re-add lon_bnds:units on disk since to_netcdf() strips matching
    # bounds attributes during serialization
    import netCDF4

    with netCDF4.Dataset(nc_path, mode="a") as nc:
        nc.variables["lon_bnds"].units = "degrees_east"

    raw = xr.open_dataset(nc_path, decode_cf=False)
    decoded = xr.open_dataset(nc_path, decode_cf=True)
    reverted = xarray_undecode_cf(decoded)

    _assert_datasets_match_raw(reverted, raw)
    assert reverted["lon_bnds"].attrs["units"] == "degrees_east"


def test_unencode_cf_invalid_type():
    """Raise TypeError for unsupported input types."""
    with pytest.raises(TypeError, match="Dataset or xarray.DataTree"):
        xarray_undecode_cf({"not": "a dataset"})  # type: ignore[arg-type]


def test_unencode_cf_datatree_subtree(data_dir):
    """unencode_cf on a non-root DataTree node rebases paths to root."""
    test_nc_path = data_dir / "test.nc"
    raw_sub = xr.open_datatree(test_nc_path, decode_cf=False)["/forecast"]
    decoded_sub = xr.open_datatree(test_nc_path, decode_cf=True)["/forecast"]

    reverted_sub = xarray_undecode_cf(decoded_sub)

    assert reverted_sub.name == "forecast"
    assert [p for p, _ in reverted_sub.subtree_with_keys] == [
        p for p, _ in raw_sub.subtree_with_keys
    ]

    for (_, raw_node), (_, rev_node) in zip(
        raw_sub.subtree_with_keys, reverted_sub.subtree_with_keys
    ):
        _assert_datasets_match_raw(
            rev_node.to_dataset(inherit=False),
            raw_node.to_dataset(inherit=False),
        )
