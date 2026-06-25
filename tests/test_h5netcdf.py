"""Check that xnetcdf is consistent with h5netcdf, where approriate."""

import h5netcdf
import numpy as np
import pytest

import xnetcdf


def test_xnetcdf_h5netcdf_attributes(data_dir):
    """Check that attributes are parsed correctly."""
    dataset = data_dir / "test.nc"
    with (
        h5netcdf.File(dataset) as h,
        xnetcdf.Dataset(dataset, backend="pyfive") as p,
    ):
        hq = h["/forecast/model/q"]
        pq = p["/forecast/model/q"]

        assert sorted(pq.attrs) == sorted(hq.attrs)

        for attr, pvalue in pq.attrs.items():
            hvalue = hq.attrs[attr]

            # h5netcdf string-valued attributes are bytes
            if isinstance(hvalue, (bytes, np.bytes_)):
                hvalue = hvalue.decode("UTF-8")

            assert type(pvalue) is type(hvalue)

            if isinstance(pvalue, (np.ndarray, np.integer, np.floating)):
                assert pvalue.dtype == hvalue.dtype
                assert np.allclose(pvalue, hvalue)
            else:
                assert pvalue == hvalue


def test_xnetcdf_h5netcdf_dimensions(data_dir):
    """Check that dimensions are parsed correctly."""
    dataset = data_dir / "test.nc"
    with (
        h5netcdf.File(dataset) as h,
        xnetcdf.Dataset(dataset, backend="pyfive") as p,
    ):
        for group in ("/", "/forecast", "/forecast/model"):
            pg = p[group]
            hg = h if group == "/" else h[group]

            assert set(hg.dimensions) == set(pg.dimensions)

            for name, pdim in pg.dimensions.items():
                ndim = hg.dimensions[name]
                assert pdim.isunlimited() == ndim.isunlimited()
                assert pdim.group().path == ndim.group().name

                for attr in ("name", "size"):
                    assert getattr(pdim, attr) == getattr(ndim, attr)


def test_xnetcdf_h5netcdf_variables(data_dir):
    """Check that variables are parsed correctly."""
    dataset = data_dir / "test.nc"
    with (
        h5netcdf.File(dataset) as h,
        xnetcdf.Dataset(dataset, backend="pyfive") as p,
    ):
        for group in ("/", "/forecast", "/forecast/model"):
            pg = p[group]
            hg = h if group == "/" else h[group]

            assert set(hg.variables) == set(pg.variables)

            for name, pvar in pg.variables.items():
                hvar = hg.variables[name]

                assert pvar.chunks == hvar.chunks
                assert len(pvar.dimensions) == len(hvar.dimensions)
                assert np.ma.allclose(pvar[...], hvar[...])

                if pvar.shape:
                    assert len(pvar) == len(hvar)
                else:
                    with pytest.raises(IndexError):
                        len(hvar)

                for attr in (
                    "shape",
                    "ndim",
                    "dtype",
                    "dimensions",
                ):
                    assert getattr(pvar, attr) == getattr(hvar, attr)


def test_xnetcdf_h5netcdf_groups(data_dir):
    """Check that groups are parsed correctly."""
    dataset = data_dir / "test.nc"
    with (
        h5netcdf.File(dataset) as h,
        xnetcdf.Dataset(dataset, backend="pyfive") as p,
    ):
        for group in ("/", "/forecast", "/forecast/model"):
            pg = p[group]
            hg = h if group == "/" else h[group]

            assert pg.attrs == hg.attrs
            assert pg.path == hg.name
