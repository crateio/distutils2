import os
from distutils2.util import iglob

__all__ = ['resources_dests']

def _expand(root_dir, glob_base, glob_suffix):
    """search for file in a directory and return they radical part.

    root_dir:    directory where to search for resources.
    glob_base:   part of the path not included in radical.
    glob_suffix: part of the path used as radical.
    """
    if glob_base:
        base = os.path.join(root_dir, glob_base)
    else:
        base = root_dir
    if '*' in base or '{' in base or '}'  in base:
        raise NotImplementedError('glob are not supported into base part\
            of resources definition. %r is an invalide root_dir' % base)
    absglob = os.path.join(base, glob_suffix)
    for glob_file in iglob(absglob):
        path_suffix = glob_file[len(base):].lstrip('/')
        relpath = glob_file[len(root_dir):].lstrip('/')
        yield relpath, path_suffix

def resources_dests(resources_dir, rules):
    """find destination of ressources files"""
    destinations = {}
    for (base, suffix, glob_dest) in rules:
        for resource_file, radical in _expand(resources_dir, base, suffix):
            if glob_dest is None:
                destinations.pop(resource_file, None) #remove the entry if it was here
            else:
                destinations[resource_file] = os.path.join(glob_dest, radical)
    return destinations
