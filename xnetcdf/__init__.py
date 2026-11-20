from importlib.metadata import PackageNotFoundError, version

from .xnetcdf import Dataset, Dimension, Group, Variable, backends

__date__ = "2026-07-01"

try:
    __version__ = version("xnetcdf")
except PackageNotFoundError as exc:
    msg = (
        "xnetcdf package not found, please run `pip install -e .` before "
        "importing the package."
    )
    raise PackageNotFoundError(
        msg,
    ) from exc
