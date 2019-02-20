"""Tab completion of paths inside an HDF5 file"""
import h5py
import sys

class H5Completer:
    """Readline tab completion for paths inside an HDF5 file"""
    def __init__(self, file: h5py.File):
        self.file = file
        self.cache = (None, [])

    def completions(self, text: str):
        if text == self.cache[0]:
            return self.cache[1]
        prev_path, _, prefix = text.rpartition('/')
        group = self.file
        if prev_path:
            group = self.file[prev_path]
            prev_path += '/'
        res = [prev_path + k + ('/' if isinstance(v, h5py.Group) else '')
               for (k, v) in group.items()
               if k.lower().startswith(prefix.lower())]
        self.cache = (text, res)
        return res

    def rlcomplete(self, text: str, state: int):
        # print(repr(text), state)
        try:
            res = self.completions(text)
        except Exception as e:
            #print(e)
            return None
        # print(repr(text), len(res))
        if state >= len(res):
            return None
        return res[state]

def main():
    """Called by shells to generate completions"""
    filename, prefix = sys.argv[1:]
    f = h5py.File(filename, 'r')
    for completion in H5Completer(f).completions(prefix):
        print(completion)

def install_hooks():
    """Install hooks for bash to complete paths in files"""
    import os, shutil
    pjoin = os.path.join
    pkgdir = os.path.dirname(os.path.abspath(__file__))
    data_home = os.environ.get('XDG_DATA_HOME', '') \
                or os.path.expanduser('~/.local/share')

    # Bash
    src = pjoin(pkgdir, 'completion.bash')
    dst_dir = pjoin(data_home, 'bash-completion/completions')
    os.makedirs(dst_dir, exist_ok=True)
    dst = pjoin(dst_dir, 'h5glance')
    shutil.copy(src, dst)
    print("Copied", dst)


if __name__ == '__main__':
    install_hooks()