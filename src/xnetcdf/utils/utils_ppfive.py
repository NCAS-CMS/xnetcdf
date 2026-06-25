"""Utilities for the `ppfive` backend."""

from .utils_general import get_dataset_name_and_protocol, get_library


def ppfive_read(dataset, options):
    """Read a dataset with `ppfive`.

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
            Additional keyword parameters to pass to `ppfive.File`.

    :Returns:

        (`ppfive.File`, `dict`, library)
            The opened dataset, the dataset's global attributes, and
            the `ppfive` library itself.

    """
    import ppfive

    dataset_name = ""
    protocol = -1

    if isinstance(dataset, ppfive.File):
        nc = dataset
        library = get_library(dataset)
        dataset_name = dataset.filename
        owns_accessor = False

        # Attempt to get the dataset name and file system protocol
        try:
            # fsspec file-like
            dataset_name = dataset._fh.path
        except AttributeError:
            try:
                # BinaryIO
                dataset_name = dataset._fh.name
            except AttributeError:
                pass
            else:
                # BinaryIO
                protocol = "file"
        else:
            try:
                # fsspec file-like
                protocol = dataset._fh.fs.protocol
            except AttributeError:
                pass

        if not dataset_name:
            dataset_name = "<ppfive-like>"

    else:
        options = options.copy()
        mode = options.pop("mode", "r")
        if mode != "r":
            raise ValueError(f"Can't set mode={mode!r} in ppfive_options")

        dataset, dataset_name, protocol = get_dataset_name_and_protocol(
            dataset
        )
        nc = ppfive.File(dataset, mode="r", **options)

        library = ppfive
        owns_accessor = True

    return {
        "dataset_name": dataset_name,
        "protocol": protocol,
        "nc": nc,
        "attrs": nc.attrs,
        "backend_api": "ppfive",
        "library": library,
        "owns_accessor": owns_accessor,
    }
