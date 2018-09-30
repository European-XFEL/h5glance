**H5Glance** lets you explore HDF5 files in the terminal or an HTML interface.

.. image:: https://travis-ci.org/European-XFEL/h5glance.svg?branch=master
    :target: https://travis-ci.org/European-XFEL/h5glance

In the terminal, you can get a tree view of a file::

    $ h5glance sample.h5
    sample.h5
    └path
      └inside
        └file	[float64: 100 × 100]

The names of datasets, groups and links are colour-coded by default.
If you want to disable this, set the environment variable ``H5GLANCE_COLORS=0``.

Inspect a group or dataset inside it::

    $ h5glance sample.h5 path/inside/file
    sample.h5/path/inside/file
          dtype: float64
          shape: 100 × 100
       maxshape: 100 × 100
         layout: Contiguous

    sample data:
    [[-0.27756437  0.36923643 -0.28113527 ...

Use ``-`` as the second argument, and you can enter the path with tab
completion::

    $ h5glance sample.h5 -
    Object path: sample.h5/  # try tapping tab

The HTML interface lets you inspect HDF5 files in a Jupyter Notebook.
`Demo.ipynb <https://nbviewer.jupyter.org/github/takluyver/h5glance/blob/master/Demo.ipynb>`_
shows how to use it.

