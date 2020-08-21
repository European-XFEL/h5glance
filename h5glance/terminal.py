"""Terminal h5glance interface for inspecting HDF5 files
"""
import argparse
import h5py
import h5py.h5o
import io
import os
import numpy
from pathlib import Path
import shlex
from shutil import get_terminal_size
from subprocess import PIPE, Popen, run
import sys

from .datatypes import fmt_dtype
from .utils import fmt_shape

layout_names = {
    h5py.h5d.COMPACT: 'Compact',
    h5py.h5d.CONTIGUOUS: 'Contiguous',
    h5py.h5d.CHUNKED: 'Chunked',
    h5py.h5d.VIRTUAL: 'Virtual',
}

def fmt_attr(key, attrs):
    """Format an attribute to show on a single line"""
    attr = attrs.get_id(key)
    shape = attr.shape
    hdf_dt = attr.get_type()

    if shape is None:
        return "empty [{}]".format(fmt_dtype(hdf_dt))

    if len(shape) <= 1:
        # For very small attributes, try to show the data inline
        try:
            v = attrs[key]
        except Exception:
            return "unreadable [{}: {}]".format(fmt_dtype(hdf_dt), shape)
        else:
            if isinstance(v, numpy.ndarray):
                return numpy.array2string(v, precision=5, threshold=10)

            sv = repr(v)  # single values, inc. strings
            if len(sv) > 50:
                sv = sv[:20] + '...' + sv[-20:]
            return sv

    # >= 2 dims
    return 'array [{}: {}]'.format(fmt_dtype(hdf_dt), shape)


def print_dataset_info(ds: h5py.Dataset, slice_expr=None, file=None):
    """Print detailed information for an HDF5 dataset."""
    print('      dtype:', fmt_dtype(ds.id.get_type()), file=file)
    print('      shape:', fmt_shape(ds.shape), file=file)
    if ds.shape:  # Skip maxshape for scalar & empty datasets
        print('   maxshape:', fmt_shape(ds.maxshape), file=file)
    layout = ds.id.get_create_plist().get_layout()
    print('     layout:', layout_names.get(layout, 'Unknown'), file=file)
    if layout == h5py.h5d.CHUNKED:
        print('      chunk:', fmt_shape(ds.chunks), file=file)
        print('compression: {} (options: {})'
              .format(ds.compression, ds.compression_opts), file=file)

    numpy.set_printoptions(threshold=numpy.inf)
    if sys.stdout.isatty():
        numpy.set_printoptions(linewidth=get_terminal_size()[0])

    if slice_expr:
        print("\nselected data [{}]:".format(slice_expr), file=file)
        try:
            arr = eval('ds[{}]'.format(slice_expr), {'ds': ds})
        except Exception as e:
            print("Error slicing", e, file=file)
        else:
            print(arr, file=file)
    elif ds.size and ds.size > 0:  # size is None for empty datasets
        print('\nsample data:', file=file)
        if ds.ndim == 0:
            print(ds[()], file=file)
        elif ds.ndim == 1:
            print(ds[:10], file=file)
        else:
            select = (0,) * (ds.ndim - 2) + (slice(0, 10),) * 2
            print(ds[select], file=file)

    print('\n{} attributes:'.format(len(ds.attrs)), file=file)
    for k in ds.attrs:
        print('* ', k, ': ', fmt_attr(k, ds.attrs), sep='', file=file)

class ColorsNone:
    dataset = group = link = reset = ''

class ColorsDefault:
    dataset = '\x1b[1m'  # Bold
    group = '\x1b[94m'   # Bright blue
    link = '\x1b[95m'    # Bright magenta
    reset = '\x1b[0m'

def use_colors():
    if os.name != 'posix':
        return False
    env = os.environ.get('H5GLANCE_COLORS', '')
    if env:
        return env != '0'
    return sys.stdout.isatty()

class TreeViewBuilder:
    """Build a tree view of an HDF5 group or file

    The tree nodes are tuples (line, children).
    """
    def __init__(self, expand_attrs=False):
        self.expand_attrs = expand_attrs
        if use_colors():
            self.colors = ColorsDefault
        else:
            self.colors = ColorsNone
        self.visited = dict()

    def object_node(self, obj, name, max_depth=numpy.inf):
        """Build a tree node for an HDF5 group/dataset
        """
        color_stop = self.colors.reset
        if isinstance(obj, h5py.Dataset):
            color_start = self.colors.dataset
        elif isinstance(obj, h5py.Group):
            color_start = self.colors.group
        else:
            color_start = ''

        obj_id = h5py.h5o.get_info(obj.id).addr

        if obj_id in self.visited:
            # Hardlink to an object we've seen before
            first_link = self.visited[obj_id]
            return (color_start + name + color_stop + '\t= ' + first_link), []

        # An object we haven't seen before
        self.visited[obj_id] = obj.name

        children = []
        detail = attr_detail = ''

        if self.expand_attrs:
            children += attrs_tree_nodes(obj)
        else:
            n = len(obj.attrs)
            attr_detail = ' ({} attributes)'.format(n) if n else ''

        if isinstance(obj, h5py.Dataset):
            detail = '\t[{dt}: {shape}]'.format(
                dt=fmt_dtype(obj.id.get_type()),
                shape=fmt_shape(obj.shape),
            )
            if obj.id.get_create_plist().get_layout() == h5py.h5d.VIRTUAL:
                detail += ' virtual'
        elif isinstance(obj, h5py.Group):
            if max_depth >= 1:
                children += [self.group_item_node(obj, key, max_depth - 1)
                             for key in obj]
            else:
                detail = f'\t({len(obj)} children)'
        else:
            detail = ' (unknown h5py type)'

        return (color_start + name + color_stop + detail + attr_detail), children

    def group_item_node(self, group, key, max_depth=numpy.inf):
        """Build a tree node for one key in a group"""
        link = group.get(key, getlink=True)
        if isinstance(link, h5py.SoftLink):
            target = link.path
        elif isinstance(link, h5py.ExternalLink):
            target = '{}/{}'.format(link.filename, link.path)
        else:
            return self.object_node(group[key], key, max_depth=max_depth)

        line = '{}{}{}\t-> {}'.format(
            self.colors.link, key, self.colors.reset, target)
        return line, []


class TreePrinter:
    """Print HDF5 groups (& optionally attributes) as a tree.
    """
    def __init__(self, file=None, expand_attrs=False):
        self.file = file or sys.stdout
        self.expand_attrs = expand_attrs
        if use_colors():
            self.colors = ColorsDefault
        else:
            self.colors = ColorsNone
        self.prefixes = []
        self.visited = dict()

    def object_node(self, obj, name, max_depth=numpy.inf, _prefix1='', _prefix2=''):
        """Build a tree node for an HDF5 group/dataset
        """
        color_stop = self.colors.reset
        if isinstance(obj, h5py.Dataset):
            color_start = self.colors.dataset
        elif isinstance(obj, h5py.Group):
            color_start = self.colors.group
        else:
            color_start = ''

        obj_id = h5py.h5o.get_info(obj.id).addr

        if obj_id in self.visited:
            # Hardlink to an object we've seen before
            first_link = self.visited[obj_id]
            print(f'{_prefix1}{color_start}{name}{color_stop}\t= {first_link}', file=self.file)
            return

        # An object we haven't seen before
        self.visited[obj_id] = obj.name

        children = []
        detail = ''

        if isinstance(obj, h5py.Dataset):
            detail = '\t[{dt}: {shape}]'.format(
                dt=fmt_dtype(obj.id.get_type()),
                shape=fmt_shape(obj.shape),
            )
            if obj.id.get_create_plist().get_layout() == h5py.h5d.VIRTUAL:
                detail += ' virtual'
        elif isinstance(obj, h5py.Group):
            if max_depth < 1:
                detail = f'\t({len(obj)} children)'
        else:
            detail = ' (unknown h5py type)'

        nattr = len(obj.attrs)
        if nattr and not self.expand_attrs:
            detail += f' ({nattr} attributes)'

        print(f'{_prefix1}{color_start}{name}{color_stop}{detail}', file=self.file)

        if nattr and self.expand_attrs:
            print(f'{_prefix2}└{nattr} attributes:')
            for i, k in enumerate(obj.attrs):
                attr_prefix = _prefix2 + '  ' + ('└' if nattr == i + 1 else '├')
                print(f'{attr_prefix}{k}: {fmt_attr(k, obj.attrs)}')

        if isinstance(obj, h5py.Group) and max_depth >= 1:
            nchild = len(obj)
            for i, k in enumerate(obj):
                islast = (nchild == i + 1)
                c_prefix1 = _prefix2 + ('└' if islast else '├')
                c_prefix2 = _prefix2 + ('  ' if islast else '│ ')
                self.group_item_node(obj, k, max_depth=max_depth - 1, _prefix1=c_prefix1, _prefix2=c_prefix2)

    def group_item_node(self, group, key, max_depth=numpy.inf, _prefix1='', _prefix2=''):
        """Build a tree node for one key in a group"""
        link = group.get(key, getlink=True)
        if isinstance(link, h5py.SoftLink):
            target = link.path
        elif isinstance(link, h5py.ExternalLink):
            target = '{}/{}'.format(link.filename, link.path)
        else:
            return self.object_node(group[key], key, max_depth=max_depth,
                                    _prefix1=_prefix1, _prefix2=_prefix2)

        print(f'{_prefix1}{self.colors.link}{key}{self.colors.reset}\t-> {target}', file=self.file)

def attrs_tree_nodes(obj):
    """Build tree nodes for attributes"""
    nattr = len(obj.attrs)
    if not nattr:
        return []

    children = [('{}: {}'.format(k, fmt_attr(k, obj.attrs)), [])
                for k in obj.attrs]
    return [('{} attributes:'.format(nattr), children)]

def print_tree(node, prefix1='', prefix2='', file=None):
    """Render a tree to show in the terminal.

    Each tree node consists of a line of text to be displayed
    and a list of child nodes.
    """
    root, children = node
    print(prefix1 + root, file=file)

    nchild = len(children)
    for i, node in enumerate(children):
        islast = (nchild == i + 1)
        c_prefix1 = prefix2 + ('└'  if islast else '├')
        c_prefix2 = prefix2 + ('  ' if islast else '│ ')
        print_tree(node, prefix1=c_prefix1, prefix2=c_prefix2, file=file)

def group_to_str(grp: h5py.Group, expand_attrs=False, max_depth=1):
    sio = io.StringIO()
    tvb = TreeViewBuilder(expand_attrs=expand_attrs)
    root = grp.file.filename + '/' + grp.name.lstrip('/')
    print_tree(tvb.object_node(grp, root, max_depth=max_depth), file=sio)
    return sio.getvalue()

def page(text):
    """Display text in a terminal pager

    Respects the PAGER environment variable if set.
    """
    pager_cmd = shlex.split(os.environ.get('PAGER') or 'less -r')
    run(pager_cmd, input=text.encode('utf-8'))


class MaybePagedOutput(io.TextIOBase):
    """Send output to a pager if it's long enough to fill the terminal.

    Temporarily captures output until either it's long enough to fill the
    terminal (when it's sent to the pager), or it's
    """
    buffer = None
    _popen = None
    lines_buffered = terminal_rows = 0

    def __init__(self):
        if sys.stdout.isatty():
            self.buffer = io.StringIO()
            _, self.terminal_rows = get_terminal_size()
        self.stream = sys.stdout

    def _dump_buffer(self):
        self.stream.write(self.buffer.getvalue())
        self.buffer = None

    def _start_pager(self):
        pager_cmd = shlex.split(os.environ.get('PAGER') or 'less -r')
        self._popen = Popen(pager_cmd, stdin=PIPE, universal_newlines=True)
        self.stream = self._popen.stdin
        self._dump_buffer()

    def writable(self) -> bool:
        return True

    def write(self, s: str):
        if self.buffer is None:
            return self.stream.write(s)

        n = self.buffer.write(s)
        self.lines_buffered += s.count('\n')
        if self.lines_buffered > self.terminal_rows:
            self._start_pager()
        return n

    def close(self):
        if self.buffer is not None:
            self.stream.write(self.buffer.getvalue())
            self.buffer = None
        if self._popen is not None:
            self._popen.stdin.close()
            self._popen.wait()
        super().close()


def display_h5_obj(file: h5py.File, path=None, expand_attrs=False, slice_expr=None):
    """Display information on an HDF5 file, group or dataset

    This is the central function for the h5glance command line tool.
    """
    if path:
        root = file.filename + '/' + path.lstrip('/')
        obj = file[path]
    else:
        root = file.filename
        obj = file

    with MaybePagedOutput() as out:
        if isinstance(obj, h5py.Group):
            if slice_expr is not None:
                sys.exit("Slicing is only allowed for datasets")
            tvb = TreePrinter(expand_attrs=expand_attrs, file=out)
            tvb.object_node(obj, root)
        elif isinstance(obj, h5py.Dataset):
            print(root, file=out)
            print_dataset_info(obj, slice_expr, file=out)
        else:
            sys.exit("What is this? " + repr(obj))

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
    ap.add_argument('-s', '--slice',
        help="Select part of a dataset to examine, using Python slicing and "
             "indexing as for a numpy array, e.g. 0,100:110",
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
        display_h5_obj(f, path, slice_expr=args.slice, expand_attrs=args.attrs)
