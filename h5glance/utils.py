"""Helper functions
"""
import h5py

_mapping = {}
_mapping[h5py.File] = "file"
_mapping[h5py.Group] = "group"
_mapping[h5py.Dataset] = "dataset"


def register_h5pyd():
    import h5pyd
    _mapping[h5pyd.File] = "file"
    _mapping[h5pyd.Group] = "group"
    _mapping[h5pyd.Dataset] = "dataset"


def check_class(obj_class):
    """Check registered class"""
    lib = obj_class.__module__.split(".")[0]
    if lib == "h5pyd":
        register_h5pyd()
    else:
        _mapping[obj_class] = None


def is_file(obj):
    """Returns true if the object is a h5py-like file."""
    obj_class = obj.__class__
    if obj_class not in _mapping:
        check_class(obj_class)
    return _mapping.get(obj_class, None) == "file"


def is_dataset(obj):
    """Returns true if the object is a h5py-like dataset."""
    obj_class = obj.__class__
    if obj_class not in _mapping:
        check_class(obj_class)
    return _mapping.get(obj_class, None) == "dataset"


def is_group(obj):
    """Returns true if the object is a h5py-like group."""
    obj_class = obj.__class__
    if obj_class not in _mapping:
        check_class(obj_class)
    return _mapping.get(obj_class, None) in ["file", "group"]
