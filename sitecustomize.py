import os
import sys


def _canonical(path):
    if not path:
        return ''
    return os.path.normcase(os.path.realpath(os.path.abspath(path)))


_root = os.path.dirname(os.path.abspath(__file__))
_src = os.path.join(_root, 'src')

seen = set()
filtered = []
for entry in sys.path:
    if entry == '':
        filtered.append(entry)
        continue
    key = _canonical(entry)
    if key in seen:
        continue
    seen.add(key)
    filtered.append(entry)
sys.path[:] = filtered

preferred = [_root, _src]
for candidate in preferred:
    canonical = _canonical(candidate)
    if any(_canonical(entry) == canonical for entry in sys.path):
        continue
    sys.path.insert(0, candidate)

# Keep the live project path and discard the Dropbox alias if both point to the same tree.
for candidate in [
    '/home/david/Dropbox/progs/python/malodos1',
    '/home/david/Dropbox/progs/python/malodos1/src',
    '/home/david/progs/python/malodos1',
    '/home/david/progs/python/malodos1/src',
]:
    real_candidate = _canonical(candidate)
    sys.path[:] = [
        entry for entry in sys.path
        if _canonical(entry) != real_candidate or entry in preferred
    ]
