"""Apply the passage-ID reader to the public artifact of a pinned historical release."""
from pathlib import Path
import shutil
import sys


def stage(site, tools):
    sys.path.insert(0, str(tools / 'scripts'))
    from profile_passages import migrate
    module = site / 'assets/passage-refs.js'
    if module.exists():
        migrate(site, check=True)
        return
    # Both entry points must resolve a profile before rendering it. Verify the
    # known historical entry points before changing any staged profile.
    edits = []
    for name, old, new in [
        ('cbr-person.js', 'cache.set(id, person.then(async p => {',
         'cache.set(id, person.then(resolveProfilePassages).then(async p => {'),
        ('cbr-person-page.js', 'const preview = await response.json();',
         'const preview = await resolveProfilePassages(await response.json());'),
    ]:
        path = site / 'assets' / name
        text = path.read_text()
        if text.count(old) != 1 or 'resolveProfilePassages' in text:
            raise ValueError(f'Unrecognized historical reader entry point {path}')
        edits.append((path, "import {resolveProfilePassages} from './passage-refs.js';\n" + text.replace(old,new)))
    updated = migrate(site)
    for path, text in edits:
        path.write_text(text)
    shutil.copyfile(tools / 'assets/passage-refs.js', module)
    print(f'Converted {updated} historical profiles in the publication artifact')


if __name__ == '__main__':
    stage(Path(sys.argv[1]), Path(sys.argv[2]))
