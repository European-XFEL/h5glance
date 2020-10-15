import h5py
import os

from .html import h5obj_to_html
from .terminal import group_to_str

class H5Glance:
    """View an HDF5 object in a Jupyter notebook"""
    def __init__(self, obj):
        self.obj = obj

    def _repr_html_(self):
        return h5obj_to_html(self.obj)

    def __repr__(self):
        if isinstance(self.obj, (str, bytes, os.PathLike)):
            with h5py.File(self.obj, 'r') as f:
                return repr(H5Glance(f))
        return group_to_str(self.obj, max_depth=1)

def install_ipython_h5py_display(html=True, text=True):
    """Call inside IPython to install HTML/text views for h5py groups and files"""
    from IPython import get_ipython
    ip = get_ipython()
    if ip is None:
        raise EnvironmentError("This function is to be called in IPython")

    if html:
        html_formatter = ip.display_formatter.formatters['text/html']
        html_formatter.for_type(h5py.Group, h5obj_to_html)
    if text:
        text_formatter = ip.display_formatter.formatters['text/plain']
        text_formatter.for_type(h5py.Group, pretty_print_group)
        text_formatter.for_type(h5py.File, pretty_print_group)

def pretty_print_group(obj, p, cycle):
    p.text(group_to_str(obj))
