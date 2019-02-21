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


def install_hooks():
    """Install hooks for bash to complete paths in files"""
    import os, shutil, subprocess
    pjoin = os.path.join
    pkgdir = os.path.dirname(os.path.abspath(__file__))
    data_home = os.environ.get('XDG_DATA_HOME', '') \
                or os.path.expanduser('~/.local/share')

    # Bash
    if shutil.which('bash'):
        src = pjoin(pkgdir, 'completion.bash')
        dst_dir = pjoin(data_home, 'bash-completion/completions')
        os.makedirs(dst_dir, exist_ok=True)
        dst = pjoin(dst_dir, 'h5glance')
        shutil.copy(src, dst)
        print("Copied", dst)

    # Zsh
    if shutil.which('zsh'):
        src = pjoin(pkgdir, 'completion.zsh')
        dst_dir = pjoin(data_home, 'zsh-completions')
        os.makedirs(dst_dir, exist_ok=True)
        dst = pjoin(dst_dir, '_h5glance')
        shutil.copy(src, dst)
        print("Copied", dst)

        stdout = subprocess.check_output(['zsh', '-i', '-c', 'echo $FPATH'])
        if dst_dir not in stdout.decode('utf-8').split(':'):
            with open(os.path.expanduser('~/.zshrc'), 'a') as f:
                f.write('\nfpath=("{}" $fpath)\ncompinit\n'.format(dst_dir))
            print("Added {} to fpath in ~/.zshrc".format(dst_dir))


if __name__ == '__main__':
    install_hooks()
