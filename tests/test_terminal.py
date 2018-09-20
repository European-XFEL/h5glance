import io
from h5glance import terminal

def test_tree_view(simple_h5_file):
    sio = io.StringIO()
    tree = terminal.object_tree_node(simple_h5_file, simple_h5_file.filename)
    terminal.print_tree(tree, file=sio)
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

def test_completer(simple_h5_file):
    comp = terminal.H5Completer(simple_h5_file)
    # Complete groups
    assert set(comp.completions('group1/sub')) == {'group1/subgroup1/', 'group1/subgroup2/'}
    # Complete a dataset - no trailing slash
    assert set(comp.completions('group1/subgroup2/')) == {'group1/subgroup2/dataset1'}
    # Case insensitive completion
    assert set(comp.completions('GRO')) == {'group1/'}
