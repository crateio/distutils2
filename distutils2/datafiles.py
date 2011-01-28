from glob import glob as simple_glob
import os
from os import path as osp


class SmartGlob(object):

    def __init__(self, base, suffix):
        self.base = base
        self.suffix = suffix


    def expand(self, basepath, category):
        if self.base:
            base = osp.join(basepath, self.base)
        else:
            base = basepath
        absglob = osp.join(base, self.suffix)
        for file in glob(absglob):
            path_suffix = file[len(base):].lstrip('/')
            relpath = file[len(basepath):].lstrip('/')
            yield relpath, osp.join(category, path_suffix)

def glob(path_glob):
    if '**' in path_glob:
        files = rglob(path_glob)
    else:
        files = simple_glob(path_glob)
    return files

def rglob(path_glob):
    prefix, radical = path_glob.split('**', 1)
    if prefix == '':
        prefix = '.'
    if radical == '':
        radical = '*'
    else:
        radical = radical.lstrip('/')
    glob_files = []
    for (path, dir, files) in os.walk(prefix):
        for file in glob(osp.join(prefix, path, radical)):
           glob_files.append(os.path.join(prefix, file))
    return glob_files

def resources_dests(resources_dir, rules):
    destinations = {}
    for (base, suffix, glob_dest) in rules:
        sglob = SmartGlob(base, suffix)
        for file, file_dest in sglob.expand(resources_dir, glob_dest):
            destinations[file] = file_dest
    return destinations
