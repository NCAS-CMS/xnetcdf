"""Utilities for the `umfive` backend."""

from .utils_general import get_dataset_name_and_protocol, get_library


def umfive_read(dataset, options):
    """Read a dataset with `umfive`.

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
            Additional keyword parameters to pass to `umfive.File`.

    :Returns:

        (`umfive.File`, `dict`, library)
            The opened dataset, the dataset's global attributes, and
            the `umfive` library itself.

    """
    import umfive

    dataset_name = ""
    protocol = -1

    if isinstance(dataset, umfive.File):
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
            dataset_name = "<umfive-like>"

    else:
        options = options.copy()
        mode = options.pop("mode", "r")
        if mode != "r":
            raise ValueError(f"Can't set mode={mode!r} in umfive_options")

        dataset, dataset_name, protocol = get_dataset_name_and_protocol(
            dataset
        )
        nc = umfive.File(dataset, mode="r", **options)

        library = umfive
        owns_accessor = True

    return {
        "dataset_name": dataset_name,
        "protocol": protocol,
        "nc": nc,
        "attrs": nc.attrs,
        "backend_api": "umfive",
        "library": library,
        "owns_accessor": owns_accessor,
    }
