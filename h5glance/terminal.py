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
from subprocess import run
import sys

def fmt_dtype(dtype):
    if dtype.metadata and 'vlen' in dtype.metadata:
        base_dtype = dtype.metadata['vlen']
        if base_dtype is str:
            return 'UTF-8 str'
        elif base_dtype is bytes:
            return 'ASCII str'
        else:
            return 'vlen {}'.format(fmt_dtype(base_dtype))
    elif dtype.fields:
        fields = ['{}: {}'.format(name, fmt_dtype(dtype.fields[name][0]))
                  for name in dtype.names]
        return '({})'.format(', '.join(fields))
    else:
        return dtype.name

def fmt_shape(shape):
    return " × ".join(('Unlimited' if n is None else str(n)) for n in shape)

layout_names = {
    h5py.h5d.COMPACT: 'Compact',
    h5py.h5d.CONTIGUOUS: 'Contiguous',
    h5py.h5d.CHUNKED: 'Chunked',
    h5py.h5d.VIRTUAL: 'Virtual',
}

def fmt_attr(v):
    if isinstance(v, numpy.ndarray):
        sv = 'array [{}: {}]'.format(fmt_dtype(v.dtype), fmt_shape(v.shape))
    else:
        sv = repr(v)
        if len(sv) > 50:
            sv = sv[:20] + '...' + sv[-20:]
    return sv

def print_dataset_info(ds: h5py.Dataset, file=None):
    """Print detailed information for an HDF5 dataset."""
    print('      dtype:', fmt_dtype(ds.dtype), file=file)
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

    print('\n{} attributes:'.format(len(ds.attrs)), file=file)
    for k, v in ds.attrs.items():
        print('* ', k, ': ', fmt_attr(v), sep='', file=file)

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

    def object_node(self, obj, name):
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
                dt=fmt_dtype(obj.dtype),
                shape=fmt_shape(obj.shape),
            )
            if obj.id.get_create_plist().get_layout() == h5py.h5d.VIRTUAL:
                detail += ' virtual'
        elif isinstance(obj, h5py.Group):
            children += [self.group_item_node(obj, key)
                         for key in obj]
        else:
            detail = ' (unknown h5py type)'

        return (color_start + name + color_stop + detail + attr_detail), children

    def group_item_node(self, group, key):
        """Build a tree node for one key in a group"""
        link = group.get(key, getlink=True)
        if isinstance(link, h5py.SoftLink):
            target = link.path
        elif isinstance(link, h5py.ExternalLink):
            target = '{}/{}'.format(link.filename, link.path)
        else:
            return self.object_node(group[key], key)

        line = '{}{}{}\t-> {}'.format(
            self.colors.link, key, self.colors.reset, target)
        return line, []

def attrs_tree_nodes(obj):
    """Build tree nodes for attributes"""
    nattr = len(obj.attrs)
    if not nattr:
        return []

    children = [('{}: {}'.format(k, fmt_attr(v)), [])
                for (k, v) in obj.attrs.items()]
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
        root = file.filename + '/' + path.lstrip('/')
        obj = file[path]
    else:
        root = file.filename
        obj = file

    if isinstance(obj, h5py.Group):
        tvb = TreeViewBuilder(expand_attrs=expand_attrs)
        print_tree(tvb.object_node(obj, root), file=sio)
    elif isinstance(obj, h5py.Dataset):
        print(root, file=sio)
        print_dataset_info(obj, file=sio)
    else:
        sys.exit("What is this? " + repr(obj))

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
