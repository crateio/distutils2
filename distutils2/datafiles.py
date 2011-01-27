from glob import glob as simple_glob
import os
from os import path as osp

def glob(path_glob):
    if '**' in path_glob:
        return rglob(path_glob)
    else:
        return simple_glob(path_glob)

def find_glob(ressources):
    destinations = {}
    for (path_glob,category) in ressources:
        project_path = os.getcwd()
        abspath_glob = osp.join(project_path, path_glob)

        for file in glob(abspath_glob):
            file = file[len(project_path):].lstrip('/')
            destinations.setdefault(file, set()).add(category)

    return destinations

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
