"""Shell integration to tab complete paths inside an HDF5 file"""
import os
import shutil
import subprocess

pjoin = os.path.join
pkgdir = os.path.dirname(os.path.abspath(__file__))

def install_hooks():
    """Install hooks for bash & zsh to complete paths in files"""
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
