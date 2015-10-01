.. tddtags documentation master file, created by
   sphinx-quickstart on Tue Jul  9 22:26:36 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to TDDTags's documentation!
======================================

Contents:

.. toctree::
   :maxdepth: 2

   readme
   installation
   usage
   contributing
   authors
   history

Need to specify the root package folder. Can run tddtag from anywhere, but generally it will be launched
from the same folder where a source module is, or from the root of the package being tested. But: will need to
allow specifying the exact anchor folder.

The unit_test_module needs to specify the full package.module to the unit test module unless it is in the
same package as the source.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
