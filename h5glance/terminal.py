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
    pager_cmd = shlex.split(os.environ.get('PAGER') or 'less -r')
    run(pager_cmd, input=text.encode('utf-8'))

def display_tree(file, groupname=None):
    sio = io.StringIO()
    if groupname:
        print(file.filename + '/' + groupname, file=sio)
        group = file[groupname]
    else:
        print(file.filename, file=sio)
        group = file
    print_paths(group, file=sio)

    output = sio.getvalue()
    if sys.stdout.isatty():
        nlines = len(output.splitlines())
        _, term_lines = get_terminal_size()
        if nlines > term_lines:
            return page(output)

    print(output)

def main(argv=None):
    ap = argparse.ArgumentParser(prog="h5glance",
             description="View HDF5 file structure in the terminal")
    ap.add_argument("input", help="HDF5 file to view", type=Path)
    args = ap.parse_args(argv)

    if not args.input.is_file():
        print("Not a file:", args.input)
        sys.exit(2)
    elif not h5py.is_hdf5(args.input):
        print("Not an HDF5 file:", args.input)
        sys.exit(2)

    with h5py.File(args.input, 'r') as f:
        display_tree(f)
