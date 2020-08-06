import h5py

from .html import h5obj_to_html

class H5Glance:
    """View an HDF5 object in a Jupyter notebook"""
    def __init__(self, obj):
        self.obj = obj

    def _repr_html_(self):
        return h5obj_to_html(self.obj)

def install_ipython_h5py_display():
    """Call inside IPython to install HTML views for h5py groups and files"""
    from IPython import get_ipython
    ip = get_ipython()
    if ip is None:
        raise EnvironmentError("This function is to be called in IPython")
    html_formatter = ip.display_formatter.formatters['text/html']
    html_formatter.for_type(h5py.Group, h5obj_to_html)
