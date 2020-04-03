from h5glance import datatypes
from h5py import h5t
import numpy as np

def test_standard_float():
    ft = h5t.py_create(np.dtype('<f4'))
    assert datatypes.fmt_dtype(ft) == 'float32'
    assert datatypes.dtype_description(ft) == '32-bit floating point'

def test_custom_float():
    f1 = h5t.IEEE_F16LE.copy()
    f1.set_fields(14, 9, 5, 0, 9)
    f1.set_size(2)
    f1.set_ebias(53)
    assert datatypes.fmt_dtype(f1) == 'custom 2-byte float'

def test_standard_int():
    it = h5t.py_create(np.dtype('<i4'))
    assert datatypes.fmt_dtype(it) == 'int32'
    assert datatypes.dtype_description(it) == '32-bit signed integer'

    ut = h5t.py_create(np.dtype('>u8'))
    assert datatypes.fmt_dtype(ut) == 'uint64 (big-endian)'
    assert datatypes.dtype_description(ut) == '64-bit unsigned integer'

def test_custom_int():
    i1 = h5t.STD_U32LE.copy()
    i1.set_size(6)
    assert datatypes.fmt_dtype(i1) == '6-byte unsigned integer'

def test_string():
    # vlen string
    vst = h5t.py_create(h5t.string_dtype(encoding='utf-8'), logical=True)
    assert datatypes.fmt_dtype(vst) == 'UTF-8 string'

    # fixed-length string
    fst = h5t.py_create(h5t.string_dtype(encoding='ascii', length=3))
    assert datatypes.fmt_dtype(fst) == '3-byte ASCII string'

def test_compound():
    ct_n = np.dtype([('x', np.float32), ('y', np.float32)])
    ct_h = h5t.py_create(ct_n)
    assert datatypes.fmt_dtype(ct_h) == '(x: float32, y: float32)'

def test_enum():
    et_n = h5t.enum_dtype({'apple': 1, 'banana': 2})
    et_h = h5t.py_create(et_n, logical=True)
    assert datatypes.fmt_dtype(et_h) == 'enum (apple, banana)'

def test_vlen():
    vt_n = h5t.vlen_dtype(np.dtype('<i2'))
    vt_h = h5t.py_create(vt_n, logical=True)
    assert datatypes.fmt_dtype(vt_h) == 'vlen array of int16'

def test_array():
    at_n = np.dtype((np.float64, (3, 4)))
    at_h = h5t.py_create(at_n)
    assert datatypes.fmt_dtype(at_h) == '3 × 4 array of float64'
