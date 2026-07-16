"""Utilities for rendering a `Dataset` in CDL."""

import numpy as np


def cdl_format(g, lines, depth=0):
    """Render a group into CDL.

    All sub-groups are also converted.

    :Parameters:

        g: `Group` or `Dataset`
            The group to render.

        lines: `list`
            A list to store the converted lines of CDL.

        depth: `int`
            The current nesting level (0 for root, 1 for first-level
            groups, etc.). Used to calculate indents for keywords
            (2*depth), members (2*depth + 5), and attributes (2*depth
            + 9).

    :Returns:

        `None`

    """
    # The structural keywords (dimensions:, variables:, group:): 0, 2,
    # 4, ...
    #
    # Root (0) -> 0 spaces
    # Sub-group (1) -> 2 spaces
    # Sub-sub-group (2) -> 4 spaces
    label_indent = " " * (2 * depth)

    # Base indentation: 1, 3, ...
    base_indent = 2 * depth + 1
    # Indentation for dimension and variable definitions: 5, 7, 9, ...
    defn_indent = " " * (base_indent + 4)
    # Indentation for attributes: 9, 11, 13, ...
    attr_indent = " " * (base_indent + 8)

    # Dimensions
    if g.dimensions:
        lines.append(f"{label_indent}dimensions:")
        for name, dim in g.dimensions.items():
            if dim.isunlimited():
                d = f"UNLIMITED ; // ({dim.size} currently)"
            else:
                d = f"{dim.size} ;"

            lines.append(f"{defn_indent}{name} = {d}")

    # Variables
    if g.variables:
        lines.append(f"{label_indent}variables:")
        for name, var in g.variables.items():
            dtype = cdl_type(var.dtype)

            dims = ", ".join(var.dimensions)
            if dims:
                dims = f"({dims})"

            lines.append(f"{defn_indent}{dtype} {name}{dims} ;")

            # Variable attributes
            for attr, value in var.attrs.items():
                pfx = "string " if cdl_is_string_list(value) else ""
                lines.append(
                    f"{attr_indent}{pfx}{name}:{attr} = "
                    f"{cdl_value(value)} ;"
                )

    # Group attributes
    if g.attrs:
        label = "group" if depth > 0 else "global"

        lines.append(f"\n{label_indent}// {label} attributes:")

        for attr, value in g.attrs.items():
            pfx = "string " if cdl_is_string_list(value) else ""
            lines.append(f"{attr_indent}{pfx}:{attr} = {cdl_value(value)} ;")

    # Recursive sub-groups
    for name, group in g.groups.items():
        lines.append(f"\n{label_indent}group: {name} {{")

        cdl_format(group, lines, depth + 1)

        # Braces are at 2, 4, 6... (match the 'group:' keyword)
        brace_indent = " " * (2 * (depth + 1))
        lines.append(f"{brace_indent}}} // group {name}")


def cdl_is_string_list(value):
    """Detect if the CDL 'string' attribute prefix is needed.

    :Parameters:

        value:
            The attribute value.

    :Returns:

         `bool`
             `True` if we need the 'string' prefix.

    """
    if isinstance(value, (list, np.ndarray, tuple)):
        return np.array(value).dtype.kind in ("S", "U")

    return False


def cdl_type(dtype):
    """Maps numpy data types CDL type keywords.

    :Parameters:

        dtype: `numpy.dtype`
            The data type.

    :Returns:

         `str`
             The formatted data type.

    """
    s = dtype.kind
    if s == "f":
        return "double" if dtype.itemsize == 8 else "float"

    if s in ("i", "u"):
        if dtype.itemsize == 1:
            return "byte"

        if dtype.itemsize == 2:
            return "short"

        if dtype.itemsize == 8:
            return "int64"

        return "int"

    if s in ("S", "U"):
        return "string"

    return str(dtype)


def cdl_value(value):
    """Format an attribute value.

    Formats an attribute value with CDL suffixes based on its numpy
    dtype.

    :Parameters:

        value:
            The attribute value.

    :Returns:

         `str`
             The formatted value.

    """
    # Handle empty arrays/lists first
    if isinstance(value, (list, np.ndarray, tuple)) and not len(value):
        return '""'

    # Ensure we are working with a numpy-friendly type to check dtypes
    dtype = getattr(value, "dtype", np.array(value).dtype)
    kind = dtype.kind
    is_array = isinstance(value, (list, np.ndarray, tuple))

    def format_el(v, k, dt):
        """Helper to apply suffixes to individual elements."""
        if k in ("S", "U"):  # Strings
            return f'"{v}"'

        if k == "f":  # Floats
            # ncdump uses 'f' for float32, and just a '.' for float64
            res = str(float(v))
            if res.endswith(".0"):
                res = res[:-1]  # "49.0" -> "49."

            return f"{res}f" if dt.itemsize == 4 else res

        if k in ("i", "u"):  # Integers
            suffix = {
                ("i", 1): "b",  # int8
                ("i", 2): "s",  # int16
                ("i", 4): "",  # int32 (default)
                ("i", 8): "LL",  # int64
                ("u", 1): "UB",  # uint8
                ("u", 2): "US",  # uint16
                ("u", 4): "U",  # uint32
                ("u", 8): "ULL",  # uint64
            }.get((k, dt.itemsize), "")
            return f"{int(v)}{suffix}"

        return str(v)

    if is_array:
        return ", ".join(format_el(x, kind, dtype) for x in value)

    return format_el(value, kind, dtype)
