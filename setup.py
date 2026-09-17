"""Create a fresh local environment and private configuration on any computer."""
from pathlib import Path
import shutil
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent / 'appium_comments_project'

def main():
    if sys.version_info < (3, 10):
        raise SystemExit('Python 3.10 or newer is required.')
    environment = ROOT / '.venv-local'
    venv.EnvBuilder(with_pip=True).create(environment)
    python = environment / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(ROOT / 'requirements.txt')], check=True)
    for source, target in [('devices.example.json', 'devices.json'), ('accounts.example.py', 'accounts.py')]:
        if not (ROOT / target).exists():
            shutil.copyfile(ROOT / source, ROOT / target)
    for name in ('comment_data.txt', 'post_urls.txt', 'follow_data.txt'):
        (ROOT / name).touch(exist_ok=True)
    print('Setup complete. Edit appium_comments_project/devices.json before starting.')

if __name__ == '__main__':
    main()
