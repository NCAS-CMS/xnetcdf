Thank you for taking the time to consider making a contribution to the `xnetcdf` package!

## General Guidelines

We greatly value contributions of any kind. Contributions could include, but are not limited to documentation improvements, bug reports, new or improved code, code reviews, infrastructure improvements, outreach improvements, and community help/building. We value the time you invest in contributing and strive to make the process as easy as possible. If you have suggestions for improving the process of contributing, please do not hesitate to propose them. 

- All questions, reports of bugs, and other suggestions for enhancements should be raised initially as GitHub issues at <https://github.com/NCAS-CMS/xnetcdf/issues>.

## Design considerations

Please keep the following considerations in mind when programming:

- changes should preferably be backward compatible.
- apply changes gradually and change no more than a few files in a single pull request (PR), but do make sure every pull request in itself brings a meaningful improvement. This reduces the risk of breaking existing functionality and making backward incompatible changes, because it helps you as well as the reviewers of your pull request to better understand what exactly is being changed;
- `xnetcdf` has very few direct dependencies (not counting the external backend libraries) - when you suggest new functionality, please bear this in mind: a brand new functionality should not require more than a few extra dependencies, if any;
- `xnetcdf`'s main scope is provide a netCDF4 enhanced data model view of dateasets, and extra functionality should not depart too far from this concept.
