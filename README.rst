**H5Glance** lets you explore HDF5 files in the terminal or an HTML interface.

.. image:: https://travis-ci.org/European-XFEL/h5glance.svg?branch=master
    :target: https://travis-ci.org/European-XFEL/h5glance

Install it with::

    pip install h5glance

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

In bash & zsh, h5glance offers tab-completion for the paths inside HDF5 files.
To set this up, run::

    python -m h5glance.completer

Alternatively, use ``-`` as the second argument, and h5glance will prompt you
for the object path with tab completion::

    $ h5glance sample.h5 -
    Object path: sample.h5/  # try tapping tab

HTML interface
--------------

The HTML interface lets you inspect HDF5 files in a Jupyter Notebook.
`Demo.ipynb <https://nbviewer.jupyter.org/github/European-XFEL/h5glance/blob/master/Demo.ipynb>`_
shows how to use it.

Why H5Glance?
-------------

There are plenty of other tools to view HDF5 files, including
`HDFView <https://www.hdfgroup.org/downloads/hdfview/>`_ and
`ViTables <https://vitables.org/>`_, as well as various web-based viewers in
development. Why might you choose H5Glance?

- Practical terminal interface: if you're working in a terminal, it's much
  quicker to use something there than to start a GUI application and click
  through it.

  - Tab completions are part of this - take a moment to set them up (see above).

- Static Jupyter views: H5Glance shows your HDF5 objects in simple HTML, which
  doesn't talk to the server. Export your notebook to HTML, or `view it on
  nbviewer <https://nbviewer.jupyter.org/github/European-XFEL/h5glance/blob/master/Demo.ipynb>`_,
  and the H5Glance view is still there.
- Deeply nested structure: It was written at `European XFEL <https://www.xfel.eu/>`_,
  where data files can easily have 6 layers of nested groups. It tries to make
  working with that easy.

Some things it's not designed for:

- Viewing data: The terminal interface can show raw data, but it focuses on the
  structure of HDF5 files, not their content. H5Glance won't show you plots or
  images.
- Machine-readable output: It's meant for people, not programs.
  In Python, your code can use `h5py <https://docs.h5py.org/en/stable/>`_.
  For shell pipelines, use tools like ``h5ls`` and ``h5dump``.

