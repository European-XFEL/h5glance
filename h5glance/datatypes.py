from functools import lru_cache
from h5py import h5t
import numpy as np
from .utils import fmt_shape

cset_names = {h5t.CSET_ASCII: 'ASCII', h5t.CSET_UTF8: 'UTF-8'}

# h5py TypeIDs are not consistently hashable, so we can't use them as dict keys.
# Instead, we look up by size, and then check equality with the standard types.
@lru_cache()
def int_types_by_size():
    d = {}
    for tc in np.typecodes['AllInteger']:
        _add_typecode(tc, d)
    return d

@lru_cache()
def float_types_by_size():
    d = {}
    for tc in np.typecodes['Float']:
        _add_typecode(tc, d)
    return d

def _add_typecode(tc, sizes_dict):
    dt_le = np.dtype('<' + tc)
    dt_be = np.dtype('>' + tc)

    entries = sizes_dict.setdefault(dt_le.itemsize, [])
    entries.append((h5t.py_create(dt_le), dt_le.name))
    entries.append((h5t.py_create(dt_be), dt_be.name + ' (big-endian)'))


def fmt_dtype(hdf_dt):
    """Get a (preferably short) string describing an HDF5 datatype"""
    size = hdf_dt.get_size()

    if isinstance(hdf_dt, h5t.TypeIntegerID):
        # Check normal int & uint dtypes first
        for candidate, descr in int_types_by_size().get(size, ()):
            if hdf_dt == candidate:
                return descr
        un = 'un' if hdf_dt.get_sign() == h5t.SGN_NONE else ''
        return "{}-byte {}signed integer".format(size, un)
    elif isinstance(hdf_dt, h5t.TypeFloatID):
        # Check normal float dtypes first
        for candidate, descr in float_types_by_size().get(size, ()):
            if hdf_dt == candidate:
                return descr
        return "custom {}-byte float".format(size)
    elif isinstance(hdf_dt, h5t.TypeBitfieldID):
        return "{}-byte bitfield".format(size)
    elif isinstance(hdf_dt, h5t.TypeTimeID):
        return "time"  # NB. time datatype is deprecated
    elif isinstance(hdf_dt, h5t.TypeOpaqueID):
        s = "{}-byte opaque".format(size)
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
            return "enum ({})".format(", ".join(
                hdf_dt.get_member_name(i).decode('utf-8', 'replace')
                for i in range(nmembers)
            ))
    elif isinstance(hdf_dt, h5t.TypeReferenceID):
        return "region ref" if hdf_dt == h5t.STD_REF_DSETREG else "object ref"

    return "unrecognised {}-byte datatype".format(size)


def dtype_description(hdf_dt):
    """A slightly longer description, suitable for a tooltip

    Can return None
    """
    size = hdf_dt.get_size()

    if isinstance(hdf_dt, h5t.TypeIntegerID):
        # Check normal int & uint dtypes first
        for candidate, descr in int_types_by_size().get(size, ()):
            if hdf_dt == candidate:
                un = 'un' if hdf_dt.get_sign() == h5t.SGN_NONE else ''
                return '{}-bit {}signed integer'.format(size * 8, un)

    elif isinstance(hdf_dt, h5t.TypeFloatID):
        # Check normal float dtypes first
        for candidate, descr in float_types_by_size().get(size, ()):
            if hdf_dt == candidate:
                return '{}-bit floating point'.format(size * 8)

    return None
