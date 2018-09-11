import io
from h5glance import terminal

def test_tree_view(simple_h5_file):
    sio = io.StringIO()
    terminal.print_paths(simple_h5_file, file=sio)
    out = sio.getvalue()
    assert '└dataset2' in out
    assert 'uint64' in out
    assert '128 × 500' in out

def test_dataset_info(simple_h5_file):
    sio = io.StringIO()
    terminal.print_dataset_info(simple_h5_file["/group1/subgroup1/dataset2"], file=sio)
    out = sio.getvalue()
    assert 'dtype: float32' in out
    assert 'shape: 2 × 128 × 500' in out
