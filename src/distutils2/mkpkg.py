#!/usr/bin/env python
#
#  Helper for automating the creation of a package by looking at you
#  current directory and asking the user questions.
#
#  Available as either a stand-alone file or callable from the distutils2
#  package:
#
#     python -m distutils2.mkpkg
#  or:
#     python mkpkg.py
#
#  Written by Sean Reifschneider <jafo@tummy.com>
#
#  TODO:
#
#  Look for a license file and automatically add the category.
#  When a .c file is found during the walk, can we add it as an extension?
#  Ask if there is a maintainer different that the author
#  Ask for the platform (can we detect this via "import win32" or something)?
#  Ask for the dependencies.
#  Ask for the Requires-Dist
#  Ask for the Provides-Dist
#  Detect scripts (not sure how.  #! outside of package?)

import os
import sys
import re
import shutil
import ConfigParser
from textwrap import dedent
from distutils2._trove import all_classifiers


helpText = {
    'name': '''
The name of the program to be packaged, usually a single word composed
of lower-case characters such as "python", "sqlalchemy", or "CherryPy".
''',
    'version': '''
Version number of the software, typically 2 or 3 numbers separated by dots
such as "1.00", "0.6", or "3.02.01".  "0.1.0" is recommended for initial
development.
''',
    'description': '''
A short summary of what this package is or does, typically a sentence 80
characters or less in length.
''',
    'author': '''
The full name of the author (typically you).
''',
    'author_email': '''
E-mail address of the package author (typically you).
''',
    'do_classifier': '''
Trove classifiers are optional identifiers that allow you to specify the
intended audience by saying things like "Beta software with a text UI
for Linux under the PSF license.  However, this can be a somewhat involved
process.
''',
    'url': '''
The home page for the package, typically starting with "http://".
''',
    'trove_license': '''
Optionally you can specify a license.  Type a string that identifies a common
license, and then you can select a list of license specifiers.
''',
    'trove_generic': '''
Optionally, you can set other trove identifiers for things such as the
human language, programming language, user interface, etc...
''',
}


def askYn(question, default=None, helptext=None):
    while True:
        answer = ask(question, default, helptext, required=True)
        if answer and answer[0].lower() in 'yn':
            return answer[0].lower()

        print '\nERROR: You must select "Y" or "N".\n'


def ask(question, default=None, helptext=None, required=True,
        lengthy=False, multiline=False):
    prompt = '%s: ' % (question,)
    if default:
        prompt = '%s [%s]: ' % (question, default)
        if default and len(question) + len(default) > 70:
            prompt = '%s\n    [%s]: ' % (question, default)
    if lengthy or multiline:
        prompt += '\n   >'

    if not helptext:
        helptext = 'No additional help available.'

    helptext = helptext.strip("\n")

    while True:
        sys.stdout.write(prompt)
        sys.stdout.flush()

        line = sys.stdin.readline().strip()
        if line == '?':
            print '=' * 70
            print helptext
            print '=' * 70
            continue
        if default and not line:
            return default
        if not line and required:
            print '*' * 70
            print 'This value cannot be empty.'
            print '==========================='
            if helptext:
                print helptext
            print '*' * 70
            continue
        return line


def buildTroveDict(classifiers):
    dict = {}
    for key in classifiers:
        subDict = dict
        for subkey in key.split(' :: '):
            if not subkey in subDict:
                subDict[subkey] = {}
            subDict = subDict[subkey]
    return dict
troveDict = buildTroveDict(all_classifiers)


class SetupClass(object):
    def __init__(self):
        self.config = None
        self.classifierDict = {}
        self.setupData = {}
        self.setupData['classifier'] = self.classifierDict
        self.setupData['packages'] = {}
        self.loadConfigFile()

    def lookupOption(self, key):
        if not self.config.has_option('DEFAULT', key):
            return None
        return self.config.get('DEFAULT', key)

    def loadConfigFile(self):
        self.config = ConfigParser.RawConfigParser()
        self.config.read(os.path.expanduser('~/.mkpkgpy'))
        self.setupData['author'] = self.lookupOption('author')
        self.setupData['author_email'] = self.lookupOption('author_email')

    def updateConfigFile(self):
        valuesDifferent = False
        for compareKey in ('author', 'author_email'):
            if self.lookupOption(compareKey) != self.setupData[compareKey]:
                valuesDifferent = True
                self.config.set('DEFAULT', compareKey,
                    self.setupData[compareKey])

        if not valuesDifferent:
            return

        self.config.write(open(os.path.expanduser('~/.pygiver'), 'w'))

    def loadExistingSetup(self):
        raise NotImplementedError

    def inspectFile(self, path):
        fp = open(path, 'r')
        try:
            for line in [fp.readline() for x in range(10)]:
                m = re.match(r'^#!.*python((?P<major>\d)(\.\d+)?)?$', line)
                if m:
                    if m.group('major') == '3':
                        self.classifierDict['Programming Language :: Python :: 3'] = 1
                    else:
                        self.classifierDict['Programming Language :: Python :: 2'] = 1
        finally:
            fp.close()

    def inspectDirectory(self):
        dirName = os.path.basename(os.getcwd())
        self.setupData['name'] = dirName
        m = re.match(r'(.*)-(\d.+)', dirName)
        if m:
            self.setupData['name'] = m.group(1)
            self.setupData['version'] = m.group(2)

        for root, dirs, files in os.walk(os.curdir):
            for file in files:
                if root == os.curdir and file == 'setup.py':
                    continue
                fileName = os.path.join(root, file)
                self.inspectFile(fileName)

                if file == '__init__.py':
                    trySrc = os.path.join(os.curdir, 'src')
                    tmpRoot = root
                    if tmpRoot.startswith(trySrc):
                        tmpRoot = tmpRoot[len(trySrc):]
                    if tmpRoot.startswith(os.path.sep):
                        tmpRoot = tmpRoot[len(os.path.sep):]

                    self.setupData['packages'][tmpRoot] = root[1 + len(os.path.sep):]

    def queryUser(self):
        self.setupData['name'] = ask('Package name', self.setupData['name'],
              helpText['name'])
        self.setupData['version'] = ask('Current version number',
              self.setupData.get('version'), helpText['version'])
        self.setupData['description'] = ask('Package description',
              self.setupData.get('description'), helpText['description'],
              lengthy=True)
        self.setupData['author'] = ask('Author name',
              self.setupData.get('author'), helpText['author'])
        self.setupData['author_email'] = ask('Author e-mail address',
              self.setupData.get('author_email'), helpText['author_email'])
        self.setupData['url'] = ask('Project URL',
              self.setupData.get('url'), helpText['url'], required=False)

        if askYn('Do you want to set Trove classifiers?',
                 helptext=helpText['do_classifier']) == 'y':
            self.setTroveClassifier()

    def setTroveClassifier(self):
        self.setTroveDevStatus(self.classifierDict)
        self.setTroveLicense(self.classifierDict)
        self.setTroveOther(self.classifierDict)

    def setTroveOther(self, classifierDict):
        if askYn('Do you want to set other trove identifiers', 'n',
                 helpText['trove_generic']) != 'y':
            return

        self.walkTrove(classifierDict, [troveDict], '')

    def walkTrove(self, classifierDict, trovePath, desc):
        trove = trovePath[-1]

        if not trove:
            return

        for key in sorted(trove.keys()):
            if len(trove[key]) == 0:
                if askYn('Add "%s"' % desc[4:] + ' :: ' + key, 'n') == 'y':
                    classifierDict[desc[4:] + ' :: ' + key] = 1
                continue

            if askYn('Do you want to set items under\n   "%s" (%d sub-items)'
                    % (key, len(trove[key])), 'n',
                    helpText['trove_generic']) == 'y':
                self.walkTrove(classifierDict, trovePath + [trove[key]],
                        desc + ' :: ' + key)

    def setTroveLicense(self, classifierDict):
        while True:
            license = ask('What license do you use',
                        helptext=helpText['trove_license'],
                        required=False)
            if not license:
                return

            licenseWords = license.lower().split(' ')

            foundList = []
            for index in range(len(all_classifiers)):
                troveItem = all_classifiers[index]
                if not troveItem.startswith('License :: '):
                    continue
                troveItem = troveItem[11:].lower()

                allMatch = True
                for word in licenseWords:
                    if not word in troveItem:
                        allMatch = False
                        break
                if allMatch:
                    foundList.append(index)

            question = 'Matching licenses:\n\n'
            for i in xrange(1, len(foundList) + 1):
                question += '   %s) %s\n' % (i, all_classifiers[foundList[i - 1]])
            question += ('\nType the number of the license you wish to use or '
                         '? to try again:')
            troveLicense = ask(question, required=False)

            if troveLicense == '?':
                continue
            if troveLicense == '':
                return
            foundIndex = foundList[int(troveLicense) - 1]
            classifierDict[all_classifiers[foundIndex]] = 1
            try:
                return
            except IndexError:
                print ("ERROR: Invalid selection, type a number from the list "
                       "above.")

    def setTroveDevStatus(self, classifierDict):
        while True:
            devStatus = ask(dedent('''\
                Please select the project status:

                1 - Planning
                2 - Pre-Alpha
                3 - Alpha
                4 - Beta
                5 - Production/Stable
                6 - Mature
                7 - Inactive

                Status'''), required=False)
            if devStatus:
                try:
                    key = {
                           '1': 'Development Status :: 1 - Planning',
                           '2': 'Development Status :: 2 - Pre-Alpha',
                           '3': 'Development Status :: 3 - Alpha',
                           '4': 'Development Status :: 4 - Beta',
                           '5': 'Development Status :: 5 - Production/Stable',
                           '6': 'Development Status :: 6 - Mature',
                           '7': 'Development Status :: 7 - Inactive',
                           }[devStatus]
                    classifierDict[key] = 1
                    return
                except KeyError:
                    print ("ERROR: Invalid selection, type a single digit "
                           "number.")

    def _dotted_packages(self, data):
        packages = sorted(data.keys())
        modified_pkgs = []
        for pkg in packages:
            pkg = pkg.lstrip('./')
            pkg = pkg.replace('/', '.')
            modified_pkgs.append(pkg)
        return modified_pkgs

    def writeSetup(self):
        if os.path.exists('setup.py'):
            shutil.move('setup.py', 'setup.py.old')

        fp = open('setup.py', 'w')
        try:
            fp.write('#!/usr/bin/env python\n\n')
            fp.write('from distutils2.core import setup\n\n')
            fp.write('setup(name=%s,\n' % repr(self.setupData['name']))
            fp.write('      version=%s,\n' % repr(self.setupData['version']))
            fp.write('      description=%s,\n'
                    % repr(self.setupData['description']))
            fp.write('      author=%s,\n' % repr(self.setupData['author']))
            fp.write('      author_email=%s,\n'
                    % repr(self.setupData['author_email']))
            if self.setupData['url']:
                fp.write('      url=%s,\n' % repr(self.setupData['url']))
            if self.setupData['classifier']:
                fp.write('      classifier=[\n')
                for classifier in sorted(self.setupData['classifier'].keys()):
                    fp.write('            %s,\n' % repr(classifier))
                fp.write('         ],\n')
            if self.setupData['packages']:
                fp.write('      packages=%s,\n'
                        % repr(self._dotted_packages(self.setupData['packages'])))
                fp.write('      package_dir=%s,\n'
                        % repr(self.setupData['packages']))
            fp.write('      #scripts=[\'path/to/script\']\n')

            fp.write('      )\n')
        finally:
            fp.close()
        os.chmod('setup.py', 0755)

        print 'Wrote "setup.py".'


def main():
    setup = SetupClass()
    setup.inspectDirectory()
    setup.queryUser()
    setup.updateConfigFile()
    setup.writeSetup()


if __name__ == '__main__':
    main()
