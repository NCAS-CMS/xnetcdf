.. _Contributing:

Contributing
============

Reporting bugs
--------------

Please report bugs via a new issue in `GitHub issue tracker
<https://github.com/NCAS-CMS/xnetcdf/issues>`_.

Feature requests
----------------

Suggestions for new features and any improvements to the
functionality, API, documentation and infrastructure can be submitted
via a new issue in the `GitHub issue tracker
<https://github.com/NCAS-CMS/xnetcdf/issues>`_.

Questions
---------

Questions, such as "how can I do this?", "why does it behave like
that?", "how can I make it faster?", etc., can be raised via a new
issue the `GitHub issue tracker
<https://github.com/NCAS-CMS/xnetcdf/issues>`_.

Preparing pull requests
-----------------------

Pull requests should follow on from a discussion in the `GitHub issue
tracker <https://github.com/NCAS-CMS/xnetcdf/issues>`_.

Fork the `xnetcdf` GitHub repository
https://github.com/NCAS-CMS/xnetcdf.

Clone your fork locally and create a branch:

.. code-block:: console
	  
    $ git clone git@github.com:<YOUR GITHUB USERNAME>/xnetcdf.git
    $ cd xnetcdf
    $ git checkout -b <your-bugfix-feature-branch-name main>

Break your edits up into reasonably-sized commits, each representing a
single logical change:

.. code-block:: console
	  
    $ git commit -a -m "<COMMIT MESSAGE>"

Create a new changelog entry in ``Changelog.rst``. The entry should be
written as:

.. code-block:: rst

   * <brief description> (https://github.com/NCAS-CMS/xnetcdf/issues/<issue number>)

Run the test suite to make sure the tests all pass:
	
.. code-block:: console

   $ cd xnetcdf
   $ pytest

Finally, make sure all commits have been pushed to the remote copy of
your fork and submit the pull request via the GitHub website, to the
``main`` branch of the https://github.com/NCAS-CMS/xnetcdf
repository. Make sure to reference the original issue in the pull
request's description.

Note that you can create the pull request while you're working on
this, as it will automatically update as you add more commits. If it
is a work in progress, you can mark it initially as a draft pull
request.

