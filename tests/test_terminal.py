import io
import os
import re
import pytest

from h5glance import terminal

@pytest.fixture(scope='module', autouse=True)
def no_color():
    os.environ['H5GLANCE_COLORS'] = '0'

def test_tree_view(simple_h5_file):
    sio = io.StringIO()
    tvb = terminal.TreeViewBuilder()
    tree = tvb.object_node(simple_h5_file, simple_h5_file.filename)
    terminal.print_tree(tree, file=sio)
    out = sio.getvalue()
    assert '└dataset2' in out
    assert 'uint64' in out
    assert '128 × 500' in out

def test_attributes(simple_h5_file):
    tvb = terminal.TreeViewBuilder()
    r1, c1 = tvb.object_node(simple_h5_file['group1'], 'group1')
    assert '2 attributes' in r1
    assert 'attributes' not in c1[0][0]

    tvb2 = terminal.TreeViewBuilder(expand_attrs=True)
    r2, c2 = tvb2.object_node(simple_h5_file['group1'], 'group1')
    assert 'attributes' not in r2
    assert '2 attributes' in c2[0][0]
    attr_lines = {node[0] for node in c2[0][1]}
    assert len(attr_lines) == 2

def test_dataset_info(simple_h5_file):
    sio = io.StringIO()
    terminal.print_dataset_info(simple_h5_file["/group1/subgroup1/dataset2"], file=sio)
    out = sio.getvalue()
    assert 'dtype: float32' in out
    assert 'shape: 2 × 128 × 500' in out

def test_compound_types(simple_h5_file):
    sio = io.StringIO()
    terminal.print_dataset_info(simple_h5_file["compound"], file=sio)
    out = sio.getvalue()
    assert 'dtype: (count: uint64, amount: float32)' in out
    assert re.search(r'\(\s*3\s*,\s*0.09\s*\)', out)

def test_vlen_types(simple_h5_file):
    sio = io.StringIO()
    terminal.print_dataset_info(simple_h5_file["prose"], file=sio)
    out = sio.getvalue()
    assert 'dtype: UTF-8 str' in out
    assert "['Lorem ipsum dolor sit amet' 'consectetur adipiscing elit']" in out

def test_hard_links(simple_h5_file):
    sio = io.StringIO()
    tvb = terminal.TreeViewBuilder()
    tree = tvb.object_node(simple_h5_file, simple_h5_file.filename)
    terminal.print_tree(tree, file=sio)
    out = sio.getvalue()
    assert 'folder\t= /group1/subgroup1' in out
    assert 'values\t= /group1/subgroup1/dataset1' in out

def test_completer(simple_h5_file):
    comp = terminal.H5Completer(simple_h5_file)
    # Complete groups
    assert set(comp.completions('group1/sub')) == {'group1/subgroup1/', 'group1/subgroup2/'}
    # Complete a dataset - no trailing slash
    assert set(comp.completions('group1/subgroup2/')) == {'group1/subgroup2/dataset1'}
    # Case insensitive completion
    assert set(comp.completions('GRO')) == {'group1/'}
