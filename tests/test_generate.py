import h5py
import os
import pytest
from tempfile import TemporaryDirectory
from h5glance import generate

@pytest.fixture(scope='module')
def simple_h5_file():
    with TemporaryDirectory() as td:
        f = h5py.File(os.path.join(td, "example.h5"))
        f.create_dataset("/group1/subgroup1/dataset1", (200,), dtype='u8')
        f.create_dataset("/group1/subgroup1/dataset2", (2, 128, 500), dtype='f4')
        f.create_dataset("/group1/subgroup2/dataset1", (12,), dtype='i2')
        yield f


def test_h5obj_to_html(simple_h5_file):
    h = generate.h5obj_to_html(simple_h5_file)
    assert 'subgroup1' in h
    assert '</div>' in h
    assert '<!DOCTYPE' not in h  # This is not a full document

def test_make_document(simple_h5_file):
    h = str(generate.make_document(simple_h5_file))
    assert 'subgroup1' in h
    assert '<!DOCTYPE' in h
