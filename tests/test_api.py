import fsspec
import netCDF4
import numpy as np
import pyfive
import pytest

import xnetcdf


def test_xnetcdf_attributes(data_dir):
    """Check that attributes are parsed correctly."""
    dataset = data_dir / "test.nc"
    with (
        netCDF4.Dataset(dataset) as n,
        xnetcdf.Dataset(dataset, backend="pyfive") as p,
    ):
        nq = n["/forecast/model/q"]
        pq = p["/forecast/model/q"]

        assert sorted(pq.attrs) == sorted(nq.ncattrs())

        for attr, pvalue in pq.attrs.items():
            nvalue = nq.getncattr(attr)

            assert type(pvalue) is type(nvalue)

            if isinstance(pvalue, (np.ndarray, np.integer, np.floating)):
                assert pvalue.dtype == nvalue.dtype
                assert np.allclose(pvalue, nvalue)
            else:
                assert pvalue == nvalue


def test_xnetcdf_dimensions(data_dir):
    """Check that dimensions are parsed correctly."""
    dataset = data_dir / "test.nc"
    with (
        netCDF4.Dataset(dataset) as n,
        xnetcdf.Dataset(dataset, backend="pyfive") as p,
    ):
        for group in ("/", "/forecast", "/forecast/model"):
            pg = p[group]
            ng = n if group == "/" else n[group]

            assert set(ng.dimensions) == set(pg.dimensions)

            for name, pdim in pg.dimensions.items():
                ndim = ng.dimensions[name]
                assert pdim.isunlimited() == ndim.isunlimited()
                assert pdim.group().path == ndim.group().path

                for attr in ("name", "size"):
                    assert getattr(pdim, attr) == getattr(ndim, attr)


def test_xnetcdf_variables(data_dir):
    """Check that variables are parsed correctly."""
    dataset = data_dir / "test.nc"
    with (
        netCDF4.Dataset(dataset) as n,
        xnetcdf.Dataset(dataset, backend="pyfive") as p,
    ):
        for group in ("/", "/forecast", "/forecast/model"):
            pg = p[group]
            ng = n if group == "/" else n[group]

            assert set(ng.variables) == set(pg.variables)

            for name, pvar in pg.variables.items():
                nvar = ng.variables[name]

                assert pvar.chunking() == nvar.chunking()
                assert len(pvar.get_dims()) == len(nvar.get_dims())
                assert np.ma.allclose(pvar[...], nvar[...])

                if pvar.shape:
                    assert len(pvar) == len(nvar)
                else:
                    with pytest.raises(TypeError):
                        len(pvar)

                for attr in (
                    "name",
                    "size",
                    "shape",
                    "ndim",
                    "dtype",
                    "dimensions",
                ):
                    assert getattr(pvar, attr) == getattr(nvar, attr)

                for pdim, ndim in zip(*(pvar.get_dims(), nvar.get_dims())):
                    assert pdim.name == ndim.name
                    assert pdim.group().path == ndim.group().path


def test_xnetcdf_groups(data_dir):
    """Check that groups are parsed correctly."""
    dataset = data_dir / "test.nc"
    with (
        netCDF4.Dataset(dataset) as n,
        xnetcdf.Dataset(dataset, backend="pyfive") as p,
    ):
        for group in ("/", "/forecast", "/forecast/model"):
            pg = p[group]
            ng = n if group == "/" else n[group]

            pattrs = pg.attrs
            nattrs = {k: ng.getncattr(k) for k in ng.ncattrs()}
            assert pattrs == nattrs
            assert pg.path == ng.path


def test_xnetcdf_Dataset_file_like(data_dir):
    """Check Dataset with a file-like input."""
    dataset = data_dir / "test.nc"
    file_like = fsspec.filesystem("local").open(dataset, "rb")

    with (
        xnetcdf.Dataset(file_like) as pfl,
        xnetcdf.Dataset(dataset, backend="pyfive") as p,
    ):
        assert (
            pfl["forecast/model/q"].dimensions
            == p["forecast/model/q"].dimensions
        )


def test_xnetcdf_Dataset_pyfive_like(data_dir):
    """Check Dataset with a pyfive.File input."""
    dataset = data_dir / "test.nc"
    py5_file = pyfive.File(dataset)
    with (
        xnetcdf.Dataset(py5_file) as py5,
        xnetcdf.Dataset(dataset, backend="pyfive") as p,
    ):
        assert (
            py5["forecast/model/q"].dimensions
            == p["forecast/model/q"].dimensions
        )


def test_xnetcdf_Dataset__repr__(data_dir):
    """Test Dataset.__repr__."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert (
            repr(p)
            == f"{p.dataset_name}: <xnetcdf.Dataset: /, 1 dimension, 1 variable, 1 group>"
        )


def test_xnetcdf_Dataset__str__(data_dir):
    """Test Dataset.__str__."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert (
            str(p)
            == f"""{p.dataset_name}: <xnetcdf.Dataset: /, 1 dimension, 1 variable, 1 group>
    Dimensions:
        bounds2: <xnetcdf.Dimension: /bounds2, size=2>
    Variables:
        time: <xnetcdf.Variable: /time, shape=(), dimensions=()>
    Groups:
        forecast: <xnetcdf.Group: /forecast, 1 dimension, 2 variables, 1 group>"""
        )


def test_xnetcdf_Dataset_bad_file():
    """Test Dataset with not a netCDF file."""
    with pytest.raises(Exception):
        xnetcdf.Dataset(3.14)


def test_xnetcdf_Dataset_backend_selection(data_dir):
    """Test Dataset with specific backend selection."""
    dataset = data_dir / "test.nc"
    # Test single backend
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p.backend_api == "pyfive"

    # Test backend list
    with xnetcdf.Dataset(dataset, backend=["pyfive", "netCDF4"]) as p:
        assert p.backend_api == "pyfive"

    # Test invalid backend
    with pytest.raises(ValueError):
        xnetcdf.Dataset(dataset, backend="invalid_backend")


def test_xnetcdf_Dataset_verbose(data_dir):
    """Test Dataset with verbose output."""
    dataset = data_dir / "test.nc"

    for v in (0, 1, -1):
        with xnetcdf.Dataset(dataset, verbose=v) as _:
            # Should not raise an error
            pass


def test_xnetcdf_Dataset_dump(data_dir):
    """Test Dataset.dump."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
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

        assert (
            p.dump(display=False, data=True)
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
            Data int32:
                31
    Groups:
        forecast: <xnetcdf.Group: /forecast, 1 dimension, 2 variables, 1 group>
            Dimensions:
                lon: <xnetcdf.Dimension: /forecast/lon, size=8, unlimited>
            Variables:
                lon_bnds: <xnetcdf.Variable: /forecast/lon_bnds, shape=(8, 2), dimensions=(/forecast/lon, /bounds2)>
                    Data float64:
                        [[  0.,  45.],
                         [ 45.,  90.],
                         [ 90., 135.],
                         [135., 180.],
                         [180., 225.],
                         [225., 270.],
                         [270., 315.],
                         [315., 360.]]
                lon: <xnetcdf.Variable: /forecast/lon, shape=(8,), dimensions=(/forecast/lon,)>
                    Attributes:
                        bounds: '/forecast/lon_bnds'
                        standard_name: 'longitude'
                        units: 'degrees_east'
                    Data float64:
                        [ 22.5,  67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]
            Groups:
                model: <xnetcdf.Group: /forecast/model, 1 dimension, 3 variables, 0 groups>
                    Attributes:
                        group_attr_1: np.int64(12)
                        group_attr_2: 'bar'
                    Dimensions:
                        lat: <xnetcdf.Dimension: /forecast/model/lat, size=5>
                    Variables:
                        lat_bnds: <xnetcdf.Variable: /forecast/model/lat_bnds, shape=(5, 2), dimensions=(/forecast/model/lat, /bounds2)>
                            Data float64:
                                [[-90., -60.],
                                 [-60., -30.],
                                 [-30.,  30.],
                                 [ 30.,  60.],
                                 [ 60.,  90.]]
                        lat: <xnetcdf.Variable: /forecast/model/lat, shape=(5,), dimensions=(/forecast/model/lat,)>
                            Attributes:
                                bounds: '/forecast/model/lat_bnds'
                                standard_name: 'latitude'
                                units: 'degrees_north'
                            Data float64:
                                [-75., -45.,   0.,  45.,  75.]
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
                            Data float32:
                                [[0.007, 0.034, 0.003, 0.014, 0.018, 0.037, 0.024, 0.029],
                                 [0.023, 0.036, 0.045, 0.062, 0.046, 0.073, 0.006, 0.066],
                                 [0.11 , 0.131, 0.124, 0.146, 0.087, 0.103, 0.057, 0.011],
                                 [0.029, 0.059, 0.039, 0.07 , 0.058, 0.072, 0.009, 0.017],
                                 [0.006, 0.036, 0.019, 0.035, 0.018, 0.037, 0.034, 0.013]]"""
        )


def test_xnetcdf_Dataset_close(data_dir):
    """Test Dataset.close."""
    dataset = data_dir / "test.nc"
    p = xnetcdf.Dataset(dataset, backend="pyfive")
    assert not p._grp._fh.closed
    p.close()
    assert p._grp._fh.closed

    py5 = pyfive.File(dataset)
    p = xnetcdf.Dataset(py5)
    assert not p._grp._fh.closed
    p.close()
    assert not p._grp._fh.closed


def test_xnetcdf_Dataset_dataset_name(data_dir):
    """Test Dataset.dataset_name."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p.dataset_name == str(dataset)
        assert p.dataset_name == p.filename


def test_xnetcdf_Dataset_ncdump(data_dir):
    """Test Dataset.ncdump."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        cdl = p.ncdump(display=False)
        assert isinstance(cdl, str)
        assert "netcdf" in cdl
        assert "dimensions:" in cdl
        assert "variables:" in cdl
        assert "bounds2 = 2" in cdl
        assert "time" in cdl
        assert "forecast" in cdl


def test_xnetcdf_Dataset_cache_metadata(data_dir):
    """Test Dataset.cache_metadata."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        # Test maximal caching
        p.cache_structural_metadata("maximal")

        # Test minimal caching
        p.cache_structural_metadata("minimal")

        # Test invalid strategy
        with pytest.raises(ValueError):
            p.cache_structural_metadata("invalid")


def test_xnetcdf_Dataset_getncattr(data_dir):
    """Test Dataset.getncattr."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p.getncattr("global_attr_1") == 3.14

    # Test non-existing attribute should raise AttributeError
    with pytest.raises(AttributeError):
        p.getncattr("nonexistent_attr")


def test_xnetcdf_Dataset_backend_library(data_dir):
    """Test Dataset.backend_library."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p.backend_library is pyfive


def test_xnetcdf_Dataset_backend_accessor(data_dir):
    """Test Dataset.backend_accessor."""
    import pyfive

    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert isinstance(p.backend_accessor, pyfive.File)


def test_xnetcdf_Dataset_all_properties(data_dir):
    """Test Dataset.all_dimensions, all_variables, all_groups."""
    # Test all_dimensions
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        all_dims = p.all_dimensions
        assert isinstance(all_dims, dict)
        assert "/bounds2" in all_dims
        assert "/forecast/lon" in all_dims
        assert "/forecast/model/lat" in all_dims

        # Test all_variables
        all_vars = p.all_variables
        assert isinstance(all_vars, dict)
        assert "/time" in all_vars
        assert "/forecast/lon" in all_vars
        assert "/forecast/model/q" in all_vars

        # Test all_groups
        all_groups = p.all_groups
        assert isinstance(all_groups, dict)
        assert "/" in all_groups
        assert "/forecast" in all_groups
        assert "/forecast/model" in all_groups


def test_xnetcdf_Dataset_protocol_is_local(data_dir):
    """Test Dataset.protocol and is_local properties."""
    # For local files
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p.protocol == "file"
        assert p.is_local

    # Test with fsspec file-like object
    file_like = fsspec.filesystem("local").open(dataset, "rb")
    with xnetcdf.Dataset(file_like) as p:
        assert p.protocol == "file"
        assert p.is_local


def test_xnetcdf_Dataset_dataset_read_log(data_dir):
    """Test Dataset.dataset_read_log."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        log = p.dataset_read_log(display=False)
        assert isinstance(log, str)
        assert "Successfully read" in log


def test_xnetcdf_Dataset_enter_exit(data_dir):
    """Test Dataset in context manager."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p.attrs["global_attr_2"] == "foo"
        assert not p._grp._fh.closed

    assert p._grp._fh.closed

    py5 = pyfive.File(dataset)
    assert not py5._fh.closed
    with xnetcdf.Dataset(py5) as p:
        assert p.attrs["global_attr_2"] == "foo"

    assert not py5._fh.closed


def test_xnetcdf_Dimension__repr__(data_dir):
    """Test Dimension.__repr__."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert (
            repr(p.dimensions["bounds2"])
            == "bounds2: <xnetcdf.Dimension: /bounds2, size=2>"
        )
        assert (
            repr(p["forecast"].dimensions["lon"])
            == "lon: <xnetcdf.Dimension: /forecast/lon, size=8, unlimited>"
        )


def test_xnetcdf_Dimension_size(data_dir):
    """Test Dimension.size."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        dim = p.dimensions["bounds2"]
        assert not dim.isunlimited()
        assert dim.size == 2

        dim = p["forecast"].dimensions["lon"]
        assert dim.isunlimited()
        assert len(dim) == 8


def test_xnetcdf_Dimension__len__(data_dir):
    """Test Dimension.__len__."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        dim = p.dimensions["bounds2"]
        assert not dim.isunlimited()
        assert len(dim) == 2

        dim = p["forecast"].dimensions["lon"]
        assert dim.isunlimited()
        assert len(dim) == 8


def test_xnetcdf_Dimension_isunlimited(data_dir):
    """Test Dimension.isunlimited."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        dim = p.dimensions["bounds2"]
        assert isinstance(dim.isunlimited(), bool)
        assert not dim.isunlimited()

        dim = p["forecast"].dimensions["lon"]
        assert isinstance(dim.isunlimited(), bool)
        assert dim.isunlimited()


def test_xnetcdf_Dimension_name(data_dir):
    """Test Dimension.name."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p.dimensions["bounds2"].name == "bounds2"
        assert p["forecast"].dimensions["lon"].name == "lon"


def test_xnetcdf_Dimension_path(data_dir):
    """Test Dimension.path."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p.dimensions["bounds2"].path == "/bounds2"
        assert p["forecast"].dimensions["lon"].path == "/forecast/lon"


def test_xnetcdf_Dimension_group(data_dir):
    """Test Dimension.group."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        group = p
        assert group.dimensions["bounds2"].group() is group

        group = p["/forecast"]
        assert group.dimensions["lon"].group() is group

        group = p["/forecast/model"]
        assert group.dimensions["lat"].group() is group


def test_xnetcdf_Dimension_parent(data_dir):
    """Test Dimension.group."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        group = p
        assert group.dimensions["bounds2"].parent is group

        group = p["/forecast"]
        assert group.dimensions["lon"].parent is group

        group = p["/forecast/model"]
        assert group.dimensions["lat"].parent is group


def test_xnetcdf_Dimension_backend_api(data_dir):
    """Test Dimension.backend_api."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p.dimensions["bounds2"].backend_api == "pyfive"


def test_xnetcdf_Dimension_backend_library(data_dir):
    """Test Dimension.library."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p.dimensions["bounds2"].backend_library is pyfive


def test_xnetcdf_Variable__repr__(data_dir):
    """Test Variable.__repr__."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert (
            repr(p["time"])
            == "time: <xnetcdf.Variable: /time, shape=(), dimensions=()>"
        )
        assert (
            repr(p["forecast/lon"])
            == "lon: <xnetcdf.Variable: /forecast/lon, shape=(8,), dimensions=(/forecast/lon,)>"
        )
        assert (
            repr(p["/forecast/model/q"])
            == "q: <xnetcdf.Variable: /forecast/model/q, shape=(5, 8), dimensions=(/forecast/model/lat, /forecast/lon)>"
        )


def test_xnetcdf_Variable_backend_accessor(data_dir):
    """Test Variable.backend_accessor."""
    import pyfive

    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert isinstance(
            p["forecast/model/q"].backend_accessor, pyfive.Dataset
        )


def test_xnetcdf_Variable_maxshape(data_dir):
    """Test Variable_maxshape."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p["time"].maxshape == ()
        assert p["forecast/lon"].maxshape == (None,)
        assert p["forecast/lon_bnds"].maxshape == (None, 2)
        assert p["forecast/model/lat"].maxshape == (5,)
        assert p["forecast/model/lat_bnds"].maxshape == (5, 2)


def test_xnetcdf_Variable_name(data_dir):
    """Test Variable.name."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p["time"].name == "time"
        assert p["/forecast/model/q"].name == "q"


def test_xnetcdf_Variable_path(data_dir):
    """Test Variable.path."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p["time"].path == "/time"
        assert p["/forecast/model/q"].path == "/forecast/model/q"


def test_xnetcdf_Variable_chunking(data_dir):
    """Test Variable.chunking."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p["/forecast/model/lat"].chunking() == "contiguous"
        assert p["/forecast/model/q"].chunking() == [5, 3]


def test_xnetcdf_Variable_chunks(data_dir):
    """Test Variable.chunks."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p["/forecast/model/lat"].chunks is None
        assert p["/forecast/model/q"].chunks == (5, 3)


def test_xnetcdf_Variable_dtype(data_dir):
    """Test Variable.dtype."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p["/time"].dtype == "int32"
        assert p["/forecast/lon"].dtype == "float64"
        assert p["/forecast/model/q"].dtype == "float32"


def test_xnetcdf_Variable_orthogonal_indexing(data_dir):
    """Test Variable.__orthogonal_indexing__ property."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert isinstance(p["/time"].__orthogonal_indexing__, bool)
        assert isinstance(p["/forecast/model/q"].__orthogonal_indexing__, bool)


def test_xnetcdf_Variable_dimension_paths(data_dir):
    """Test Variable.dimension_paths property."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p["/time"].dimension_paths == ()
        assert p["/forecast/lon"].dimension_paths == ("/forecast/lon",)
        assert p["/forecast/model/q"].dimension_paths == (
            "/forecast/model/lat",
            "/forecast/lon",
        )


def test_xnetcdf_Variable_shards(data_dir):
    """Test Variable.shards property."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        # For non-zarr datasets, shards should be None
        assert p["/forecast/model/q"].shards is None


def test_xnetcdf_Variable_ndim(data_dir):
    """Test Variable.ndim."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p["/time"].ndim == 0
        assert p["/forecast/lon"].ndim == 1
        assert p["/forecast/model/q"].ndim == 2


def test_xnetcdf_Variable_shape(data_dir):
    """Test Variable.shape."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p["/time"].shape == ()
        assert p["/forecast/lon"].shape == (8,)
        assert p["/forecast/model/q"].shape == (5, 8)


def test_xnetcdf_Variable_size(data_dir):
    """Test Variable.size."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p["/time"].size == 1
        assert p["/forecast/lon"].size == 8
        assert p["/forecast/model/q"].size == 40


def test_xnetcdf_Variable__len__(data_dir):
    """Test Variable.__len__."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        with pytest.raises(TypeError):
            len(p["/time"])

        assert len(p["/forecast/lon"]) == 8
        assert len(p["/forecast/model/q"]) == 5


def test_xnetcdf_Variable_dimensions(data_dir):
    """Test Variable.dimensions."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p["/time"].dimensions == ()
        assert p["/forecast/lon"].dimensions == ("lon",)
        assert p["/forecast/model/q"].dimensions == ("lat", "lon")


def test_xnetcdf_Variable_get_dims(data_dir):
    """Test Variable.__len__."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p["/time"].get_dims() == ()
        assert p["/forecast/lon"].get_dims() == (
            p["/forecast"].dimensions["lon"],
        )
        assert p["/forecast/model/q"].get_dims() == (
            p["/forecast/model"].dimensions["lat"],
            p["/forecast"].dimensions["lon"],
        )


def test_xnetcdf_Variable_parent(data_dir):
    """Test Variable.parent."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p["/time"].parent is p
        assert p["/forecast/lon"].parent is p["/forecast"]
        assert p["/forecast/model/q"].parent is p["/forecast/model"]


def test_xnetcdf_Variable_group(data_dir):
    """Test Variable.group."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p["/time"].group() is p
        assert p["/forecast/lon"].group() is p["/forecast"]
        assert p["/forecast/model/q"].group() is p["/forecast/model"]


def test_xnetcdf_Variable_getValue(data_dir):
    """Test Variable.getValue."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        # Test scalar variable
        assert p["/time"].getValue() == 31

        # Test non-scalar variable should raise IndexError
        with pytest.raises(IndexError):
            p["/forecast/lon"].getValue()


def test_xnetcdf_Variable_getncattr(data_dir):
    """Test Variable.getncattr."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        var = p["/forecast/model/q"]

        # Test existing attribute
        assert var.getncattr("standard_name") == "specific_humidity"
        assert var.getncattr("int") == 49

        # Test non-existing attribute should raise AttributeError
        with pytest.raises(AttributeError):
            var.getncattr("nonexistent_attr")


def test_xnetcdf_Variable_ncattrs(data_dir):
    """Test Variable.ncattrs."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        var = p["/forecast/model/q"]
        attrs = var.ncattrs()
        assert isinstance(attrs, list)
        assert "standard_name" in attrs
        assert "int" in attrs
        assert set(attrs) == set(var.attrs.keys())


def test_xnetcdf_Group__repr__(data_dir):
    """Test Group.__repr__."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert (
            repr(p["/forecast"])
            == "forecast: <xnetcdf.Group: /forecast, 1 dimension, 2 variables, 1 group>"
        )

        assert (
            repr(p["/forecast/model"])
            == "model: <xnetcdf.Group: /forecast/model, 1 dimension, 3 variables, 0 groups>"
        )


def test_xnetcdf_Group__str__(data_dir):
    """Test Group.__str__."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert (
            str(p["/forecast"])
            == """forecast: <xnetcdf.Group: /forecast, 1 dimension, 2 variables, 1 group>
    Dimensions:
        lon: <xnetcdf.Dimension: /forecast/lon, size=8, unlimited>
    Variables:
        lon_bnds: <xnetcdf.Variable: /forecast/lon_bnds, shape=(8, 2), dimensions=(/forecast/lon, /bounds2)>
        lon: <xnetcdf.Variable: /forecast/lon, shape=(8,), dimensions=(/forecast/lon,)>
    Groups:
        model: <xnetcdf.Group: /forecast/model, 1 dimension, 3 variables, 0 groups>"""
        )

        assert (
            str(p["/forecast/model"])
            == """model: <xnetcdf.Group: /forecast/model, 1 dimension, 3 variables, 0 groups>
    Dimensions:
        lat: <xnetcdf.Dimension: /forecast/model/lat, size=5>
    Variables:
        lat_bnds: <xnetcdf.Variable: /forecast/model/lat_bnds, shape=(5, 2), dimensions=(/forecast/model/lat, /bounds2)>
        lat: <xnetcdf.Variable: /forecast/model/lat, shape=(5,), dimensions=(/forecast/model/lat,)>
        q: <xnetcdf.Variable: /forecast/model/q, shape=(5, 8), dimensions=(/forecast/model/lat, /forecast/lon)>"""
        )


def test_xnetcdf_Group_dump(data_dir):
    """Test Group.dump."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert (
            p["/forecast"].dump(display=False)
            == """forecast: <xnetcdf.Group: /forecast, 1 dimension, 2 variables, 1 group>
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

        assert (
            p["/forecast/model"].dump(display=False)
            == """model: <xnetcdf.Group: /forecast/model, 1 dimension, 3 variables, 0 groups>
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


def test_xnetcdf_Group__getitem__(data_dir):
    """Test Group.__getitem__."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p[""] is p
        assert p["/"] is p
        assert p["//"] is p
        assert p["/."] is p
        assert p["."] is p
        assert p["./"] is p
        assert p["./."] is p
        assert p["/./."] is p
        assert p["/././"] is p
        assert p["forecast"] is p["/forecast"]
        assert p["forecast"] is p["/forecast/"]
        assert p["forecast/model"] is p["forecast"]["model"]
        assert p["/forecast/model/"] is p["/forecast"]["model/"]
        assert p["forecast"]["/forecast/model/"] is p["/forecast/model"]
        assert p["forecast"]["/"] is p["/"]
        assert p["forecast"][""] is p["/forecast"]
        assert p["forecast"]["."] is p["/forecast"]
        assert p["forecast"]["./"] is p["/forecast"]
        assert p["forecast"]["/forecast"] is p["/forecast"]
        assert p["forecast"]["/forecast/model/q"] is p["/forecast/model/q"]
        assert p["/forecast/model/q/"] is p["/forecast/model/q"]
        assert p["/forecast//model///q////"] is p["/forecast/model/q"]
        assert p["/forecast/model/q"] is p["/forecast"]["model"]["q"]
        assert p["forecast/.."] is p["/"]
        assert p["/forecast/.."] is p["/"]
        assert p["/forecast/./.."] is p["/"]
        assert p["./forecast/./.."] is p["/"]
        assert p["./forecast/./../forecast/model/.."] is p["/forecast"]
        assert p["/forecast"][""] is p["/forecast"]
        assert p["/forecast"]["."] is p["/forecast"]
        assert p["/forecast"]["./"] is p["/forecast"]
        assert p["/forecast"][".."] is p
        assert p["/forecast"]["../"] is p

        # Test bad paths from the root group
        current_group = p["/"]
        for bad_group in (
            "/..",
            "./..",
            "/bad_group",
            "bad_group",
            "/forecast/bad_group",
            "/forecast/model/q/subgroup",
            "/forecast/model/q/..",
            "/forecast/model/q/.",
            "/forecast/model/q/./",
        ):
            with pytest.raises(KeyError):
                current_group[bad_group]

        # Test bad paths from a sub-group
        current_group = p["/forecast"]
        for bad_group in (
            "../..",
            "./../..",
            "../bad_group",
            "../model/.././bad_group",
            "/bad_group",
            "bad_group",
            "/forecast/bad_group",
            "/forecast/model/q/subgroup",
            "/forecast/model/q/..",
            "/forecast/model/q/.",
            "/forecast/model/q/./",
            "model/bad_group",
            "model/q/subgroup",
        ):
            with pytest.raises(KeyError):
                current_group[bad_group]


def test_xnetcdf_Group__iter__(data_dir):
    """Test Group.__iter__."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert tuple(p) == ("forecast", "time")
        assert tuple(p["/forecast"]) == ("model", "lon_bnds", "lon")
        assert tuple(p["/forecast/model"]) == ("lat_bnds", "lat", "q")


def test_xnetcdf_Group_keys(data_dir):
    """Test Group.keys."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert tuple(p.keys()) == ("forecast", "time")
        assert tuple(p["/forecast"].keys()) == ("model", "lon_bnds", "lon")
        assert tuple(p["/forecast/model"].keys()) == ("lat_bnds", "lat", "q")


def test_xnetcdf_Group_values(data_dir):
    """Test Group.values."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        group = p
        assert tuple(p.values()) == (group["forecast"], group["time"])

        group = p["/forecast"]
        assert tuple(group.values()) == (
            group["model"],
            group["lon_bnds"],
            group["lon"],
        )

        group = p["/forecast/model"]
        assert tuple(group.values()) == (
            group["lat_bnds"],
            group["lat"],
            group["q"],
        )


def test_xnetcdf_Group_items(data_dir):
    """Test Group.items."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        group = p
        assert tuple(group.items()) == (
            ("forecast", group["forecast"]),
            ("time", group["time"]),
        )

        group = p["/forecast"]
        assert tuple(group.items()) == (
            ("model", group["model"]),
            ("lon_bnds", group["lon_bnds"]),
            ("lon", group["lon"]),
        )

        group = p["/forecast/model"]
        assert tuple(group.items()) == (
            ("lat_bnds", group["lat_bnds"]),
            ("lat", group["lat"]),
            ("q", group["q"]),
        )


def test_xnetcdf_Group_backend_accessor(data_dir):
    """Test Group.backend_accessor."""
    import pyfive

    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert isinstance(p["forecast"].backend_accessor, pyfive.Group)


def test_xnetcdf_Group_name(data_dir):
    """Test Group.name."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p.name == ""
        assert p["/forecast"].name == "forecast"
        assert p["/forecast/model"].name == "model"


def test_xnetcdf_Group_path(data_dir):
    """Test Group.path."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        for path in ("/", "/forecast", "/forecast/model"):
            assert p[path].path == path


def test_xnetcdf_Group_parent(data_dir):
    """Test Group.parent."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p.parent is None
        assert p["/forecast"].parent is p
        assert p["/forecast/model"].parent is p["/forecast"]


def test_xnetcdf_Group_is_sub_group(data_dir):
    """Test Group.is_sub_group."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p.is_sub_group(p)
        assert p["forecast"].is_sub_group(p["forecast"])
        assert p["forecast"].is_sub_group(p)
        assert p["forecast/model"].is_sub_group(p)
        assert p["forecast/model"].is_sub_group(p["forecast"])

        assert not p.is_sub_group(p["forecast"])
        assert not p.is_sub_group(p["forecast/model"])
        assert not p["forecast"].is_sub_group(p["forecast/model"])


def test_xnetcdf_Group_is_ancestor_group(data_dir):
    """Test Group.is_ancestor_group."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        assert p.is_ancestor_group(p)
        assert p.is_ancestor_group(p["forecast"])
        assert p.is_ancestor_group(p["forecast/model"])
        assert p["forecast"].is_ancestor_group(p["forecast"])
        assert p["forecast"].is_ancestor_group(p["forecast/model"])

        assert not p["forecast"].is_ancestor_group(p)
        assert not p["forecast/model"].is_ancestor_group(p)
        assert not p["forecast/model"].is_ancestor_group(p["forecast"])


def test_xnetcdf_zarr_dimension_search(data_dir):
    """Test zarr_dimension_search parameter."""
    dataset = data_dir / "test.zarr3"
    # Test different search strategies
    for strategy in ["closest_ancestor", "furthest_ancestor", "local"]:
        with xnetcdf.Dataset(dataset, zarr_dimension_search=strategy) as p:
            assert p.backend_api == "zarr"


def test_xnetcdf_Group_getncattr(data_dir):
    """Test Group.getncattr."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        # Test root group attributes
        assert p.getncattr("global_attr_1") == 3.14

        # Test subgroup attributes
        model_group = p["/forecast/model"]
        assert model_group.getncattr("group_attr_1") == 12
        assert model_group.getncattr("group_attr_2") == "bar"

        # Test non-existing attribute should raise AttributeError
        with pytest.raises(AttributeError):
            p.getncattr("nonexistent_attr")


def test_xnetcdf_Group_ncattrs(data_dir):
    """Test Group.ncattrs."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        # Test root group
        attrs = p.ncattrs()
        assert isinstance(attrs, list)
        assert "Conventions" in attrs
        assert "global_attr_1" in attrs
        assert set(attrs) == set(p.attrs.keys())

        # Test subgroup
        model_group = p["/forecast/model"]
        attrs = model_group.ncattrs()
        assert "group_attr_1" in attrs
        assert "group_attr_2" in attrs
        assert set(attrs) == set(model_group.attrs.keys())


def test_xnetcdf_edge_cases(data_dir):
    """Test various edge cases and error conditions."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        # Test Group.__len__
        assert len(p) == 2  # forecast group + time variable
        assert len(p["/forecast"]) == 3  # model group + 2 variables

        # Test Group.get() method (inherited from Mapping)
        assert p.get("time") is p["time"]
        assert p.get("nonexistent") is None
        assert p.get("nonexistent", "default") == "default"

        # Test Variable array access with different indices
        var = p["/forecast/lon"]
        assert var[0] == 22.5
        assert np.array_equal(var[:2], [22.5, 67.5])

        # Test scalar variable indexing
        var = p["/time"]
        assert var[()] == 31


def test_xnetcdf_ncdump(data_dir):
    """Test Dataset.ncdump."""
    dataset = data_dir / "test.nc"
    with xnetcdf.Dataset(dataset, backend="pyfive") as p:
        # NOTE: Don't use a f-string here, other wise you have to
        #       escape all of the curly brackets.
        assert (
            p.ncdump(display=False)
            == "netcdf "
            + p.dataset_name
            + """ {
dimensions:
     bounds2 = 2 ;
variables:
     int time ;
         time:standard_name = "time" ;
         time:units = "days since 2018-12-01" ;

// global attributes:
         :Conventions = "CF-1.13" ;
         :global_attr_1 = 3.14 ;
         :global_attr_2 = "foo" ;

group: forecast {
  dimensions:
       lon = UNLIMITED ; // (8 currently)
  variables:
       double lon_bnds(lon, bounds2) ;
       double lon(lon) ;
           lon:bounds = "/forecast/lon_bnds" ;
           lon:standard_name = "longitude" ;
           lon:units = "degrees_east" ;

  group: model {
    dimensions:
         lat = 5 ;
    variables:
         double lat_bnds(lat, bounds2) ;
         double lat(lat) ;
             lat:bounds = "/forecast/model/lat_bnds" ;
             lat:standard_name = "latitude" ;
             lat:units = "degrees_north" ;
         float q(lat, lon) ;
             q:cell_methods = "area: mean" ;
             q:coordinates = "time" ;
             q:float = 49. ;
             q:float32 = 49.f ;
             q:float64 = 49. ;
             q:int = 49LL ;
             q:int16 = 49s ;
             q:int32 = 49 ;
             q:int64 = 49LL ;
             q:int8 = 49b ;
             q:list1 = 2b, 3b ;
             q:list10 = "" ;
             string q:list11 = "a", "bb", "ccc" ;
             string q:list12 = "a", "1", "2.5" ;
             q:list13 = "a" ;
             string q:list14 = "a", "bb" ;
             q:list2 = 2s, 3s ;
             q:list3 = 2LL, 3LL ;
             q:list4 = 2, 3 ;
             q:list5 = 2.f, 3.f ;
             q:list6 = 2., 3. ;
             q:list7 = 2LL, 3LL ;
             q:list8 = 2 ;
             q:list9 = "" ;
             q:standard_name = "specific_humidity" ;
             q:string1 = "1" ;
             q:string2 = "a" ;
             q:string3 = "kg m-2" ;
             q:string4 = "" ;
             q:string5 = " " ;
             q:string6 = "" ;
             q:string7 = "" ;
             q:string8 = "" ;
             q:string9 = "" ;
             q:uint16 = 49US ;
             q:uint32 = 49U ;
             q:uint64 = 49ULL ;
             q:uint8 = 49UB ;

    // group attributes:
             :group_attr_1 = 12LL ;
             :group_attr_2 = "bar" ;
    } // group model
  } // group forecast
}"""
        )
