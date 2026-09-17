"""Build an allowlisted source ZIP, excluding all local input and runtime data."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent

def source_files():
    files = [ROOT / name for name in ('README.md', '.gitignore', 'setup.py', 'build_portable.py')]
    files.extend(ROOT.glob('*.bat'))
    project = ROOT / 'appium_comments_project'
    for pattern in ('*.py', '*.ps1', 'README.md', 'requirements.txt', 'devices.example.json'):
        files.extend(p for p in project.glob(pattern)
                     if p.name not in ('accounts.py', 'accounts copy.py', 'comment_text.py'))
    for directory in ('instagram_actions', 'utils'):
        files.extend((project / directory).glob('*.py'))
    return sorted(set(files))

def main():
    output = ROOT / 'dist' / 'appium-comments-project.zip'
    output.parent.mkdir(exist_ok=True)
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        for path in source_files():
            archive.write(path, Path('appium-comments-project') / path.relative_to(ROOT))
    print(f'Created {output} ({len(source_files())} source files)')

if __name__ == '__main__':
    main()
