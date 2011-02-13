import os
from distutils2.util import iglob

def _rel_path(base, path):
    assert path.startswith(base)
    return path[len(base):].lstrip('/')

def resources_dests(resources_root, rules):
    """find destination of ressources files"""
    destinations = {}
    for (base, suffix, dest) in rules:
        prefix = os.path.join(resources_root, base)
        for abs_base in iglob(prefix):
            abs_glob = os.path.join(abs_base, suffix)
            for abs_path in iglob(abs_glob):
                resource_file = _rel_path(resources_root, abs_path)
                if dest is None: #remove the entry if it was here
                    destinations.pop(resource_file, None)
                else:
                    rel_path = _rel_path(abs_base, abs_path)
                    destinations[resource_file] = os.path.join(dest, rel_path)
    return destinations
