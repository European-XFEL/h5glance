"""Terminal h5glance interface for inspecting HDF5 files
"""
import argparse
import h5py
import io
import os
import shlex
from pathlib import Path
from shutil import get_terminal_size
from subprocess import run
import sys

def detail_for(obj):
    """Detail for an HDF5 object, to display by its name in the tree view.
    """
    if isinstance(obj, h5py.Dataset):
        detail = '\t[{dt}: {shape}]'.format(
            dt=obj.dtype.name,
            shape=" × ".join(str(n) for n in obj.shape),
        )
        if obj.id.get_create_plist().get_layout() == h5py.h5d.VIRTUAL:
            detail += ' virtual'
        return detail
    elif isinstance(obj, h5py.Group):
        return ''
    else:
        return ' (unknown h5py type)'

def print_paths(group, prefix='', file=None):
    """Visit and print name of all element in HDF5 file (from S Hauf)"""
    nkeys = len(group.keys())
    for i, (k, obj) in enumerate(group.items()):
        islast = (nkeys == i + 1)
        print(prefix, ('└' if islast else '├'), k, detail_for(obj),
              sep='', file=file)
        if isinstance(obj, h5py.Group):
            print_paths(obj, prefix + ('  ' if islast else '│ '), file=file)

def page(text):
    """Display text in a terminal pager

    Respects the PAGER environment variable if set.
    """
    pager_cmd = shlex.split(os.environ.get('PAGER') or 'less -r')
    run(pager_cmd, input=text.encode('utf-8'))

def display_h5_obj(file: h5py.File, path=None):
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
        print_paths(obj, file=sio)
    else:
        print(detail_for(obj), file=sio)

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
    ap = argparse.ArgumentParser(prog="h5glance",
             description="View HDF5 file structure in the terminal")
    ap.add_argument("file", help="HDF5 file to view", type=Path)
    ap.add_argument("path", nargs='?',
        help="Object to show within the file, or '-' to prompt for a name"
    )

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
        display_h5_obj(f, path)
