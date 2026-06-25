import xnetcdf


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
        assert p1.dump(display=False, data=True) == p2.dump(
            display=False, data=True
        )


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
        assert p1.dump(display=False, data=True) == p2.dump(
            display=False, data=True
        )


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
        assert p1.dump(display=False, data=True) == p2.dump(
            display=False, data=True
        )

    x._mm_buf = None
    x.close()


def test_ppfive_1(data_dir):
    """Test ppfive functionality."""
    dataset = data_dir / "test2.pp"
    with xnetcdf.Dataset(dataset, backend="ppfive") as p:
        assert p.backend_api == "ppfive"
        assert (
            p.dump(display=False)
            == f"""{p.dataset_name}: <xnetcdf.Dataset: /, 5 dimensions, 9 variables, 0 groups>
    Attributes:
        Conventions: 'CF-1.14'
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
        region: <xnetcdf.Variable: /region, shape=(3,), dimensions=(/site,)>"""
        )


def test_ppfive_2(data_dir):
    """Test ppfive functionality."""
    import ppfive

    dataset = data_dir / "test2.pp"
    with ppfive.File(dataset) as x:
        with (
            xnetcdf.Dataset(dataset, backend="ppfive") as p1,
            xnetcdf.Dataset(x, backend="ppfive") as p2,
        ):
            assert p1.backend_api == "ppfive"
            assert p2.backend_api == "ppfive"
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
    with xarray.open_datatree(
        dataset, mask_and_scale=False, decode_cf=False
    ) as x:
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
