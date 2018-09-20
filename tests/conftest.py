import h5py
import numpy
import os
import pytest
from tempfile import TemporaryDirectory

@pytest.fixture(scope='module')
def simple_h5_file():
    with TemporaryDirectory() as td:
        f = h5py.File(os.path.join(td, "example.h5"))
        f.create_dataset("/group1/subgroup1/dataset1", (200,), dtype='u8')
        f.create_dataset("/group1/subgroup1/dataset2", (2, 128, 500), dtype='f4')
        f.create_dataset("/group1/subgroup2/dataset1", (12,), dtype='i2')
        f['group1'].attrs['string'] = 'foo'
        f['group1'].attrs['array'] = numpy.zeros((3, 4))
        yield f
