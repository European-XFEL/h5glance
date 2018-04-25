import h5py
from htmlgen import Document, Element, Division, UnorderedList, Checkbox, Label, ListItem
from pathlib import Path
import sys

_PKGDIR = Path(__file__).parent

class Style(Element):
    def __init__(self, styles):
        super().__init__('style')
        self.children.append_raw(styles)

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
    return ListItem(name)

def item_for_group(gname, grp):
    subgroups, datasets = [], []
    for name, obj in grp.items():
        if isinstance(obj, h5py.Group):
            subgroups.append((name, obj))
        else:
            datasets.append((name, obj))

    return ListItem(*checkbox_w_label(gname), make_list(
        *[item_for_group(n, g) for n, g in subgroups],
        *[item_for_dataset(n, d) for n, d in datasets],
    ))

def main():
    d = Document()
    with (_PKGDIR / 'treeview.css').open() as f:
        d.append_head(Style(f.read()))

    filename = sys.argv[1]
    with h5py.File(filename, 'r') as f:
        tv = Division(make_list(item_for_group(filename, f)))
    tv.add_css_classes("css-treeview")
    d.append_body(tv)

    with open("test_output.html", 'w') as f:
        f.write(str(d))

if __name__ == '__main__':
    main()
