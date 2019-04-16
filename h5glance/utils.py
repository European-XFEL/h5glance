"""Helper functions
"""
import h5py

try:
    import h5pyd
except ImportError:
    h5pyd = None


def is_file(obj):
    """Returns true if the object is a h5py-like file."""
    if isinstance(obj, h5py.File):
        return True
    if h5pyd is not None and isinstance(obj, h5pyd.File):
        return True
    return False


def is_dataset(obj):
    """Returns true if the object is a h5py-like dataset."""
    if isinstance(obj, h5py.Dataset):
        return True
    if h5pyd is not None and isinstance(obj, h5pyd.Dataset):
        return True
    return False


def is_group(obj):
    """Returns true if the object is a h5py-like group."""
    if isinstance(obj, h5py.Group):
        return True
    if h5pyd is not None and isinstance(obj, h5pyd.Group):
        return True
    return False
