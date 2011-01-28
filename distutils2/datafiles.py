from glob import glob as simple_glob
import os
from os import path as osp


class SmartGlob(object):

    def __init__(self, path_glob):
        self.path_glob = path_glob
        if '**' in path_glob:
            self.base = path_glob.split('**', 1)[0] # XXX not exactly what we want
        else:
            self.base = osp.dirname(path_glob)


    def expand(self, basepath, category):
        for file in glob(osp.join(basepath, self.path_glob)):
            file = file[len(basepath):].lstrip('/')
            suffix = file[len(self.base):].lstrip('/')
            yield file, osp.join(category, suffix)

def glob(path_glob):
    if '**' in path_glob:
        return rglob(path_glob)
    else:
        return simple_glob(path_glob)

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
    for (path_glob, glob_dest) in rules:
        sglob = SmartGlob(path_glob)
        for file, file_dest in sglob.expand(resources_dir, glob_dest):
            destinations[file] = file_dest
    return destinations
