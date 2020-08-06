from h5glance import html


def test_h5obj_to_html(simple_h5_file):
    h = html.h5obj_to_html(simple_h5_file)
    assert 'subgroup1' in h
    assert '</div>' in h
    assert '<!DOCTYPE' not in h  # This is not a full document

def test_make_document(simple_h5_file):
    h = str(html.make_document(simple_h5_file))
    assert 'subgroup1' in h
    assert '<!DOCTYPE' in h
