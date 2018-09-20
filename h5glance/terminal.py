"""Terminal h5glance interface for inspecting HDF5 files
"""
import argparse
import h5py
import io
import os
import numpy
from pathlib import Path
import shlex
from shutil import get_terminal_size
from subprocess import run
import sys

def fmt_shape(shape):
    return " × ".join(('Unlimited' if n is None else str(n)) for n in shape)

layout_names = {
    h5py.h5d.COMPACT: 'Compact',
    h5py.h5d.CONTIGUOUS: 'Contiguous',
    h5py.h5d.CHUNKED: 'Chunked',
    h5py.h5d.VIRTUAL: 'Virtual',
}

def print_dataset_info(ds: h5py.Dataset, file=None):
    """Print detailed information for an HDF5 dataset."""
    print('      dtype:', ds.dtype.name, file=file)
    print('      shape:', fmt_shape(ds.shape), file=file)
    print('   maxshape:', fmt_shape(ds.maxshape), file=file)
    layout = ds.id.get_create_plist().get_layout()
    print('     layout:', layout_names.get(layout, 'Unknown'), file=file)
    if layout == h5py.h5d.CHUNKED:
        print('      chunk:', fmt_shape(ds.chunks), file=file)
        print('compression: {} (options: {})'
              .format(ds.compression, ds.compression_opts), file=file)

    if sys.stdout.isatty():
        numpy.set_printoptions(linewidth=get_terminal_size()[0])

    print('\nsample data:', file=file)
    if ds.ndim == 0:
        print(ds[()], file=file)
    elif ds.ndim == 1:
        print(ds[:10], file=file)
    else:
        select = (0,) * (ds.ndim - 2) + (slice(0, 10),) * 2
        print(ds[select], file=file)

def detail_for(obj, link, inc_n_attrs=False):
    """Detail for an HDF5 object, to display by its name in the tree view."""
    if isinstance(link, h5py.SoftLink):
        return '\t-> {}'.format(link.path)
    elif isinstance(link, h5py.ExternalLink):
        return '\t-> {}/{}'.format(link.filename, link.path)

    if isinstance(obj, h5py.Dataset):
        detail = '\t[{dt}: {shape}]'.format(
            dt=obj.dtype.name,
            shape=fmt_shape(obj.shape),
        )
        if obj.id.get_create_plist().get_layout() == h5py.h5d.VIRTUAL:
            detail += ' virtual'
    elif isinstance(obj, h5py.Group):
        detail = ''
    else:
        return ' (unknown h5py type)'

    if inc_n_attrs:
        n = len(obj.attrs)
        if n:
            detail += ' + {} attributes'

    return detail

def print_group_attrs(group, prefix='', file=None):
    nattr = len(group.attrs)
    if not nattr:
        return

    grp_empty = len(group) == 0
    print(prefix, ('└' if grp_empty else '├'), nattr, ' attributes:',
          sep='', file=file)

    prefix += ('  ' if grp_empty else '│ ')
    for i, (k, v) in enumerate(group.attrs.items()):
        islast = (nattr == i + 1)
        sv = str(v)
        if len(sv) > 50:
            sv = sv[:20] + '...' + sv[-20:]
        print(prefix, ('└' if islast else '├'), k, ': ', sv,
              sep='', file=file)

def print_paths(group, prefix='', file=None, expand_attrs=False):
    """Visit and print name of all element in HDF5 file (from S Hauf)"""
    nkeys = len(group.keys())
    for i, (k, obj) in enumerate(group.items()):
        islast = (nkeys == i + 1)
        link = group.get(k, getlink=True)
        detail = detail_for(obj, link, inc_n_attrs=(not expand_attrs))
        print(prefix, ('└' if islast else '├'), k, detail,
              sep='', file=file)

        # Recurse into groups, but not soft links to groups
        if isinstance(obj, h5py.Group) and isinstance(link, h5py.HardLink):
            if expand_attrs:
                print_group_attrs(obj, prefix + ('  ' if islast else '│ '), file=file)
            print_paths(obj, prefix + ('  ' if islast else '│ '), file=file)

def page(text):
    """Display text in a terminal pager

    Respects the PAGER environment variable if set.
    """
    pager_cmd = shlex.split(os.environ.get('PAGER') or 'less -r')
    run(pager_cmd, input=text.encode('utf-8'))

def display_h5_obj(file: h5py.File, path=None, expand_attrs=False):
    """Display information on an HDF5 file, group or dataset

    This is the central function for the h5glance command line tool.
    """
    sio = io.StringIO()
    if path:
        print(file.filename + '/' + path.lstrip('/'), file=sio)
        obj = file[path]
    else:
        print(file.filename, file=sio)
        obj = file

    if isinstance(obj, h5py.Group):
        if expand_attrs:
            print_group_attrs(obj, file=sio)
        print_paths(obj, file=sio)
    elif isinstance(obj, h5py.Dataset):
        print_dataset_info(obj, file=sio)
    else:
        print("What is this?", repr(obj), file=sio)

    # If the output has more lines than the terminal, display it in a pager
    output = sio.getvalue()
    if sys.stdout.isatty():
        nlines = len(output.splitlines())
        _, term_lines = get_terminal_size()
        if nlines > term_lines:
            return page(output)

    print(output)

class H5Completer:
    """Readline tab completion for paths inside an HDF5 file"""
    def __init__(self, file: h5py.File):
        self.file = file
        self.cache = (None, [])

    def completions(self, text: str):
        if text == self.cache[0]:
            return self.cache[1]
        prev_path, _, prefix = text.rpartition('/')
        group = self.file
        if prev_path:
            group = self.file[prev_path]
            prev_path += '/'
        res = [prev_path + k + ('/' if isinstance(v, h5py.Group) else '')
               for (k, v) in group.items()
               if k.lower().startswith(prefix.lower())]
        self.cache = (text, res)
        return res

    def rlcomplete(self, text: str, state: int):
        # print(repr(text), state)
        try:
            res = self.completions(text)
        except Exception as e:
            #print(e)
            return None
        # print(repr(text), len(res))
        if state >= len(res):
            return None
        return res[state]

def prompt_for_path(filename):
    """Prompt the user for a path inside the HDF5 file"""
    import readline
    with h5py.File(filename, 'r') as f:
        compl = H5Completer(f)
        readline.set_completer(compl.rlcomplete)
        readline.set_completer_delims('')
        readline.parse_and_bind("tab: complete")
        while True:
            res = input("Object path: {}/".format(filename))
            if f.get(res) is not None:
                print()
                return res
            print("No object at", repr(res))


def main(argv=None):
    from . import __version__
    ap = argparse.ArgumentParser(prog="h5glance",
             description="View HDF5 file structure in the terminal")
    ap.add_argument("file", help="HDF5 file to view", type=Path)
    ap.add_argument("path", nargs='?',
        help="Object to show within the file, or '-' to prompt for a name"
    )
    ap.add_argument('--attrs', action='store_true',
        help="Show attributes of groups",
    )
    ap.add_argument('--version', action='version',
                    version='H5glance {}'.format(__version__))

    args = ap.parse_args(argv)

    if not args.file.is_file():
        print("Not a file:", args.file)
        sys.exit(2)
    elif not h5py.is_hdf5(args.file):
        print("Not an HDF5 file:", args.file)
        sys.exit(2)

    path = args.path
    if path == '-':
        path = prompt_for_path(args.file)

    with h5py.File(args.file, 'r') as f:
        display_h5_obj(f, path, expand_attrs=args.attrs)
