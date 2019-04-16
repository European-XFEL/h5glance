"""Helper functions
"""
import h5py


def is_file(obj):
    """Returns true if the object is a h5py-like file."""
    return isinstance(obj, h5py.File)


def is_dataset(obj):
    """Returns true if the object is a h5py-like dataset."""
    return isinstance(obj, h5py.Dataset)


def is_group(obj):
    """Returns true if the object is a h5py-like group."""
    return isinstance(obj, h5py.Group)
