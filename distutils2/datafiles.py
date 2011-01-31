import os
from distutils2.util import iglob

__all__ = ['iglob', 'resources_dests']

class SmartGlob(object):

    def __init__(self, base, suffix):
        self.base = base
        self.suffix = suffix


    def expand(self, basepath, destination):
        if self.base:
            base = os.path.join(basepath, self.base)
        else:
            base = basepath
        if '*' in base or '{' in base or '}'  in base:
            raise NotImplementedError('glob are not supported into base part\
                of datafiles definition. %r is an invalide basepath' % base)
        absglob = os.path.join(base, self.suffix)
        for glob_file in iglob(absglob):
            path_suffix = glob_file[len(base):].lstrip('/')
            relpath = glob_file[len(basepath):].lstrip('/')
            dest = os.path.join(destination, path_suffix)
            yield relpath, dest

def resources_dests(resources_dir, rules):
    destinations = {}
    for (base, suffix, glob_dest) in rules:
        sglob = SmartGlob(base, suffix)
        if glob_dest is None:
            delete = True
            dest = ''
        else:
            delete = False
            dest = glob_dest
        for resource_file, file_dest in sglob.expand(resources_dir, dest):
            if delete and resource_file in destinations:
                del destinations[resource_file]
            else:
                destinations[resource_file] = file_dest
    return destinations
