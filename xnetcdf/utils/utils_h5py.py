"""Utilities for the `h5py` backend."""

from .utils_general import get_dataset_name_and_protocol, get_library


def h5py_read(dataset, options):
    """Read a dataset with the `h5py`.

    :Parameters:

        dataset:
            The definition of the dataset to be read. One of:

            * string-like (such as `str` or `pathlib.Path`)
            * file-like (such as `io.BufferedReader` or the result
                         of an `fsspec` file system open)
            * directory-like (such as `fsspec.mapping.FSMap`)

             An exception is raised if the *dataset* can't be
             interpreted.

        options: `dict`
            Additional keyword parameters to pass to `h5py.File`.

    :Returns:

        (`h5py.File`, `dict`, library)
            The opened dataset, the dataset's global attributes, and
            the `h5py` library itself.

    """
    import h5py

    dataset_name = ""
    protocol = -1

    if isinstance(dataset, h5py.File):
        nc = dataset
        library = get_library(dataset)
        dataset_name = dataset.filename
        owns_accessor = False
        if not dataset_name:
            dataset_name = "<h5py-like>"

    else:
        options = options.copy()
        mode = options.pop("mode", "r")
        if mode != "r":
            raise ValueError(f"Can't set mode={mode!r} in h5py_options")

        dataset, dataset_name, protocol = get_dataset_name_and_protocol(
            dataset
        )
        nc = h5py.File(dataset, mode="r", **options)

        library = h5py
        owns_accessor = True

    return {
        "dataset_name": dataset_name,
        "protocol": protocol,
        "nc": nc,
        "attrs": nc.attrs,
        "backend_api": "h5py",
        "library": library,
        "owns_accessor": owns_accessor,
    }
