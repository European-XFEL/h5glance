import h5py
import numpy
import os
import pytest
from tempfile import TemporaryDirectory

@pytest.fixture(scope='module')
def simple_h5_file():
    with TemporaryDirectory() as td:
        f = h5py.File(os.path.join(td, 'example.h5'), 'w')
        f.create_group('group1')
        f.create_dataset('group1/subgroup1/dataset1', (200,), dtype='u8')
        f.create_dataset('group1/subgroup1/dataset2', (2, 128, 500), dtype='f4')
        f.create_dataset('group1/subgroup2/dataset1', (12,), dtype='i2')
        f.create_dataset('group1/scalar', shape=(), dtype='i4')
        f.create_dataset('group1/empty', shape=None, dtype='i4')
        f.create_dataset('compound',
            data=numpy.array([(1, 0.5), (3, 0.090)],
                             dtype=numpy.dtype([('count', 'u8'), ('amount', 'f4')])))
        f.create_dataset('prose',
            data=numpy.array(['Lorem ipsum dolor sit amet', 'consectetur adipiscing elit'],
                             dtype=h5py.special_dtype(vlen=str)))
        f['group1'].attrs['string'] = 'foo'
        f['group1'].attrs['array'] = numpy.zeros((3, 4))
        f['synonyms/folder'] = f['group1/subgroup1']
        f['synonyms/values'] = f['group1/subgroup1/dataset1']
        yield f
        f.close()

@pytest.fixture()
def file_with_custom_float(tmp_path):
    # create a custom type with larger bias
    mytype = h5py.h5t.IEEE_F16LE.copy()
    mytype.set_fields(14, 9, 5, 0, 9)
    mytype.set_size(2)
    mytype.set_ebias(53)
    mytype.lock()

    shape = (3, 4)
    space = h5py.h5s.create_simple(shape)

    with h5py.File(str(tmp_path / 'sample.h5'), 'w') as f:
        h5py.h5d.create(f.id, b'a', mytype, space)
        yield f
