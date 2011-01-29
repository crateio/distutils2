import os
import re
from os import path as osp
from glob import iglob as simple_iglob


class SmartGlob(object):

    def __init__(self, base, suffix):
        self.base = base
        self.suffix = suffix


    def expand(self, basepath, category):
        if self.base:
            base = osp.join(basepath, self.base)
        else:
            base = basepath
        if '*' in base or '{' in base or '}'  in base:
            raise NotImplementedError('glob are not supported into base part of datafiles definition. %r is an invalide basepath' % base)
        absglob = osp.join(base, self.suffix)
        for file in iglob(absglob):
            path_suffix = file[len(base):].lstrip('/')
            relpath = file[len(basepath):].lstrip('/')
            yield relpath, osp.join(category, path_suffix)

RICH_GLOB = re.compile(r'\{([^}]*)\}')

# r'\\\{' match "\{"

def iglob(path_glob):
    rich_path_glob = RICH_GLOB.split(path_glob, 1)
    if len(rich_path_glob) > 1:
        assert len(rich_path_glob) == 3, rich_path_glob
        prefix, set, suffix = rich_path_glob
        for item in set.split(','):
            for path in iglob( ''.join((prefix, item, suffix))):
                yield path
    else:
        if '**' not in path_glob:
            for item in simple_iglob(path_glob):
                yield item
        else:
            prefix, radical = path_glob.split('**', 1)
            if prefix == '':
                prefix = '.'
            if radical == '':
                radical = '*'
            else:
                radical = radical.lstrip('/')
            for (path, dir, files) in os.walk(prefix):
                for file in iglob(osp.join(prefix, path, radical)):
                   yield os.path.join(prefix, file)

def resources_dests(resources_dir, rules):
    destinations = {}
    for (base, suffix, glob_dest) in rules:
        sglob = SmartGlob(base, suffix)
        for file, file_dest in sglob.expand(resources_dir, glob_dest):
            destinations[file] = file_dest
    return destinations
