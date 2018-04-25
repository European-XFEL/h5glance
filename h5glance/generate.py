import h5py
from htmlgen import (Document, Element, Division, UnorderedList, Checkbox,
                     Label, ListItem, html_attribute, Span,
                     )
from pathlib import Path

_PKGDIR = Path(__file__).parent

class Style(Element):
    def __init__(self, styles):
        super().__init__('style')
        self.children.append_raw(styles)

class Abbreviation(Element):
    def __init__(self, *content, title=""):
        super().__init__("abbr")
        self.extend(content)
        self.title = title

    title = html_attribute('title')

class Code(Element):
    """An HTML in-line <code> element.
    """
    def __init__(self, *content):
        super().__init__("code")
        self.extend(content)

dtype_kind_to_descr = {
    "u": "unsigned integer",
    "i": "signed integer",
    "f": "floating point",
    "c": "complex floating point",
    "b": "boolean",
    "O": "object (e.g. string)",
}

def make_dtype_abbr(dtobj):
    desc = ""
    if dtobj.kind in "uifc":
        desc += "{}-bit ".format(dtobj.itemsize * 8)
    try:
        desc += dtype_kind_to_descr[dtobj.kind]
    except KeyError:
        pass
    code = Code(dtobj.str)
    if desc:
        return Abbreviation(code, title=desc)
    return code

def make_list(*items):
    ul = UnorderedList()
    ul.extend(items)
    return ul

checkbox_id_no = [0]

def checkbox_w_label(label_content):
    c = Checkbox()
    id_no = checkbox_id_no[0]
    checkbox_id_no[0] += 1
    c.id = "item-%d" % id_no
    l = Label(label_content)
    l.for_ = c.id
    return [c, l]

def item_for_dataset(name, ds):
    shape = " × ".join(str(n) for n in ds.shape)
    namespan = Span(name)
    namespan.add_css_classes("h5glance-dataset-name")
    li = ListItem(
        namespan, ": ",
        shape, " entries, dtype: ", make_dtype_abbr(ds.dtype)
    )
    li.add_css_classes("h5glance-dataset")
    return li

def item_for_group(gname, grp):
    subgroups, datasets = [], []
    for name, obj in sorted(grp.items()):
        if isinstance(obj, h5py.Group):
            subgroups.append((name, obj))
        else:
            datasets.append((name, obj))

    return ListItem(*checkbox_w_label(gname), make_list(
        *[item_for_group(n, g) for n, g in subgroups],
        *[item_for_dataset(n, d) for n, d in datasets],
    ))

def make_fragment(obj):
    if isinstance(obj, h5py.File):
        ct = make_list(item_for_group(obj.filename, obj))
    elif isinstance(obj, h5py.Group):
        ct = make_list(item_for_group(obj.name, obj))
    elif isinstance(obj, str) and h5py.is_hdf5(obj):
        with h5py.File(obj, 'r') as f:
            return make_fragment(f)
    else:
        raise TypeError("Unknown object type: {!r}".format(obj))

    # Expand first level
    first_chkbx = ct.children.children[0].children.children[0] # Yuck
    first_chkbx.checked = True

    tv = Division(ct)
    tv.add_css_classes("h5glance-css-treeview")
    return tv

def get_treeview_css():
    with (_PKGDIR / 'treeview.css').open() as f:
        return Style(f.read())

def make_document(obj):
    d = Document()
    d.append_head(get_treeview_css())
    d.append_body(make_fragment(obj))
    return d

def h5obj_to_html(obj):
    div = Division(
        get_treeview_css(),
        make_fragment(obj),
    )
    return str(div)

class H5Glance:
    """View an HDF5 object in a Jupyter notebook"""
    def __init__(self, obj):
        self.obj = obj

    def _repr_html_(self):
        return h5obj_to_html(self.obj)
