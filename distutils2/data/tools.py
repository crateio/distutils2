from glob import glob

def check_glob(ressources):
    correspondence = {}
    for (path_glob,category) in ressources:
        filepaths = glob(path_glob)
        for filepath in filepaths:
            if not filepath in correspondence:
                correspondence[filepath] = []
            if not category in correspondence[filepath]:
                correspondence[filepath].append(category)
    return correspondence