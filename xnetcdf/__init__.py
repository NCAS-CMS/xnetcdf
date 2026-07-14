from .xnetcdf import Dataset, Group, Variable, Dimension, backends

__date__ = "2026-07-01"

from importlib.metadata import PackageNotFoundError

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
