from h5py import h5t
import numpy as np
from .utils import fmt_shape

cset_names = {h5t.CSET_ASCII: 'ASCII', h5t.CSET_UTF8: 'UTF-8'}

_std_numeric_dtypes = None


class StdNumerics:
    """Quick lookup for standard numeric datatypes

    covers signed & unsigned ints, floats & complex, as defined in numpy.
    """
    def __init__(self):
        self.by_size = {}

        for tc in np.typecodes['AllInteger'] + np.typecodes['AllFloat']:
            dt_le = np.dtype('<' + tc)
            dt_be = np.dtype('>' + tc)

            entries = self.by_size.setdefault(dt_le.itemsize, [])
            entries.append((h5t.py_create(dt_le), dt_le.name))
            entries.append((h5t.py_create(dt_be), dt_be.name + ' (big-endian)'))

    def lookup(self, hdf_dt, size):
        for candidate, descr in self.by_size.get(size, ()):
            if hdf_dt == candidate:
                return descr


def fmt_dtype(hdf_dt):
    """Get a (preferably short) string describing an HDF5 datatype"""
    global _std_numeric_dtypes

    if _std_numeric_dtypes is None:
        _std_numeric_dtypes = StdNumerics()

    size = hdf_dt.get_size()

    # Check most common cases, e.g. uint16 or float64
    res = _std_numeric_dtypes.lookup(hdf_dt, size)
    if res is not None:
        return res

    if isinstance(hdf_dt, h5t.TypeIntegerID):
        return "custom {}-byte integer".format(size)
    elif isinstance(hdf_dt, h5t.TypeFloatID):
        return "custom {}-byte float".format(size)
    elif isinstance(hdf_dt, h5t.TypeBitfieldID):
        return "{}-byte bitfield"
    elif isinstance(hdf_dt, h5t.TypeTimeID):
        return "time"  # NB. time datatype is deprecated
    elif isinstance(hdf_dt, h5t.TypeOpaqueID):
        s = "{}-byte opaque"
        tag = hdf_dt.get_tag()
        if tag:
            s += ' ({})'.format(tag.decode('utf-8', 'replace'))
        return s
    elif isinstance(hdf_dt, h5t.TypeStringID):
        cset = cset_names.get(hdf_dt.get_cset(), '?cset')
        if hdf_dt.is_variable_str():
            return "{} string".format(cset)
        else:
            return "{}-byte {} string".format(size, cset)
    elif isinstance(hdf_dt, h5t.TypeVlenID):
        return "vlen array of " + fmt_dtype(hdf_dt.get_super())
    elif isinstance(hdf_dt, h5t.TypeArrayID):
        shape = fmt_shape(hdf_dt.get_array_dims())
        return "{} array of {}".format(shape, fmt_dtype(hdf_dt.get_super()))

    elif isinstance(hdf_dt, h5t.TypeCompoundID):
        return "({})".format(", ".join(
            "{}: {}".format(
                hdf_dt.get_member_name(i).decode('utf-8', 'replace'),
                fmt_dtype(hdf_dt.get_member_type(i))
            )
            for i in range(hdf_dt.get_nmembers())
        ))
    elif isinstance(hdf_dt, h5t.TypeEnumID):
        nmembers = hdf_dt.get_nmembers()
        if nmembers >= 5:
            return "enum ({} options)".format(nmembers)
        else:
            return "enum " + ", ".join(
                hdf_dt.get_member_name(i) for i in range(nmembers)
            )
    elif isinstance(hdf_dt, h5t.TypeReferenceID):
        return "region ref" if hdf_dt == h5t.STD_REF_DSETREG else "object ref"

    return "unrecognised {}-byte datatype".format(size)
