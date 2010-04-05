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
#    Look for a license file and automatically add the category.
#
#    When a .c file is found during the walk, can we add it as an extension?
#
#    Ask if the author is the maintainer?
#
#    Ask for the platform (can we detect this via "import win32" or something)?
#
#    Ask for the dependencies.
#
#    Ask for the Requires-Dist
#
#    Ask for the Provides-Dist
#
#    Detect scripts (not sure how.  #! outside of package?)

import sys, os, re, shutil, ConfigParser


helpText = {
   'name' : '''
The name of the program to be packaged, usually a single word composed
of lower-case characters such as "python", "sqlalchemy", or "CherryPy".
''',
   'version' : '''
Version number of the software, typically 2 or 3 numbers separated by dots
such as "1.00", "0.6", or "3.02.01".  "0.1.0" is recommended for initial
development.
''',
   'description' : '''
A short summary of what this package is or does, typically a sentence 80
characters or less in length.
''',
   'author' : '''
The full name of the author (typically you).
''',
   'author_email' : '''
E-mail address of the package author (typically you).
''',
   'do_classifier' : '''
Trove classifiers are optional identifiers that allow you to specify the
intended audience by saying things like "Beta software with a text UI
for Linux under the PSF license.  However, this can be a somewhat involved
process.
''',
   'url' : '''
The home page for the package, typically starting with "http://".
''',
   'trove_license' : '''
Optionally you can specify a license.  Type a string that identifies a common
license, and then you can select a list of license specifiers.
''',
   'trove_generic' : '''
Optionally, you can set other trove identifiers for things such as the
human language, programming language, user interface, etc...
''',
}

troveList = [
        'Development Status :: 1 - Planning',
        'Development Status :: 2 - Pre-Alpha',
        'Development Status :: 3 - Alpha',
        'Development Status :: 4 - Beta',
        'Development Status :: 5 - Production/Stable',
        'Development Status :: 6 - Mature',
        'Development Status :: 7 - Inactive',
        'Environment :: Console',
        'Environment :: Console :: Curses',
        'Environment :: Console :: Framebuffer',
        'Environment :: Console :: Newt',
        'Environment :: Console :: svgalib',
        'Environment :: Handhelds/PDA\'s',
        'Environment :: MacOS X',
        'Environment :: MacOS X :: Aqua',
        'Environment :: MacOS X :: Carbon',
        'Environment :: MacOS X :: Cocoa',
        'Environment :: No Input/Output (Daemon)',
        'Environment :: Other Environment',
        'Environment :: Plugins',
        'Environment :: Web Environment',
        'Environment :: Web Environment :: Buffet',
        'Environment :: Web Environment :: Mozilla',
        'Environment :: Web Environment :: ToscaWidgets',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications',
        'Environment :: X11 Applications :: Gnome',
        'Environment :: X11 Applications :: GTK',
        'Environment :: X11 Applications :: KDE',
        'Environment :: X11 Applications :: Qt',
        'Framework :: BFG',
        'Framework :: Buildout',
        'Framework :: Chandler',
        'Framework :: CubicWeb',
        'Framework :: Django',
        'Framework :: IDLE',
        'Framework :: Paste',
        'Framework :: Plone',
        'Framework :: Pylons',
        'Framework :: Setuptools Plugin',
        'Framework :: Trac',
        'Framework :: TurboGears',
        'Framework :: TurboGears :: Applications',
        'Framework :: TurboGears :: Widgets',
        'Framework :: Twisted',
        'Framework :: ZODB',
        'Framework :: Zope2',
        'Framework :: Zope3',
        'Intended Audience :: Customer Service',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Financial and Insurance Industry',
        'Intended Audience :: Healthcare Industry',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Legal Industry',
        'Intended Audience :: Manufacturing',
        'Intended Audience :: Other Audience',
        'Intended Audience :: Religion',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Telecommunications Industry',
        'License :: Aladdin Free Public License (AFPL)',
        'License :: DFSG approved',
        'License :: Eiffel Forum License (EFL)',
        'License :: Free For Educational Use',
        'License :: Free For Home Use',
        'License :: Free for non-commercial use',
        'License :: Freely Distributable',
        'License :: Free To Use But Restricted',
        'License :: Freeware',
        'License :: Netscape Public License (NPL)',
        'License :: Nokia Open Source License (NOKOS)',
        'License :: OSI Approved',
        'License :: OSI Approved :: Academic Free License (AFL)',
        'License :: OSI Approved :: Apache Software License',
        'License :: OSI Approved :: Apple Public Source License',
        'License :: OSI Approved :: Artistic License',
        'License :: OSI Approved :: Attribution Assurance License',
        'License :: OSI Approved :: BSD License',
        'License :: OSI Approved :: Common Public License',
        'License :: OSI Approved :: Eiffel Forum License',
        'License :: OSI Approved :: European Union Public Licence 1.0 (EUPL 1.0)',
        'License :: OSI Approved :: European Union Public Licence 1.1 (EUPL 1.1)',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'License :: OSI Approved :: GNU Free Documentation License (FDL)',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'License :: OSI Approved :: IBM Public License',
        'License :: OSI Approved :: Intel Open Source License',
        'License :: OSI Approved :: ISC License (ISCL)',
        'License :: OSI Approved :: Jabber Open Source License',
        'License :: OSI Approved :: MIT License',
        'License :: OSI Approved :: MITRE Collaborative Virtual Workspace License (CVW)',
        'License :: OSI Approved :: Motosoto License',
        'License :: OSI Approved :: Mozilla Public License 1.0 (MPL)',
        'License :: OSI Approved :: Mozilla Public License 1.1 (MPL 1.1)',
        'License :: OSI Approved :: Nethack General Public License',
        'License :: OSI Approved :: Nokia Open Source License',
        'License :: OSI Approved :: Open Group Test Suite License',
        'License :: OSI Approved :: Python License (CNRI Python License)',
        'License :: OSI Approved :: Python Software Foundation License',
        'License :: OSI Approved :: Qt Public License (QPL)',
        'License :: OSI Approved :: Ricoh Source Code Public License',
        'License :: OSI Approved :: Sleepycat License',
        'License :: OSI Approved :: Sun Industry Standards Source License (SISSL)',
        'License :: OSI Approved :: Sun Public License',
        'License :: OSI Approved :: University of Illinois/NCSA Open Source License',
        'License :: OSI Approved :: Vovida Software License 1.0',
        'License :: OSI Approved :: W3C License',
        'License :: OSI Approved :: X.Net License',
        'License :: OSI Approved :: zlib/libpng License',
        'License :: OSI Approved :: Zope Public License',
        'License :: Other/Proprietary License',
        'License :: Public Domain',
        'License :: Repoze Public License',
        'Natural Language :: Afrikaans',
        'Natural Language :: Arabic',
        'Natural Language :: Bengali',
        'Natural Language :: Bosnian',
        'Natural Language :: Bulgarian',
        'Natural Language :: Catalan',
        'Natural Language :: Chinese (Simplified)',
        'Natural Language :: Chinese (Traditional)',
        'Natural Language :: Croatian',
        'Natural Language :: Czech',
        'Natural Language :: Danish',
        'Natural Language :: Dutch',
        'Natural Language :: English',
        'Natural Language :: Esperanto',
        'Natural Language :: Finnish',
        'Natural Language :: French',
        'Natural Language :: German',
        'Natural Language :: Greek',
        'Natural Language :: Hebrew',
        'Natural Language :: Hindi',
        'Natural Language :: Hungarian',
        'Natural Language :: Icelandic',
        'Natural Language :: Indonesian',
        'Natural Language :: Italian',
        'Natural Language :: Japanese',
        'Natural Language :: Javanese',
        'Natural Language :: Korean',
        'Natural Language :: Latin',
        'Natural Language :: Latvian',
        'Natural Language :: Macedonian',
        'Natural Language :: Malay',
        'Natural Language :: Marathi',
        'Natural Language :: Norwegian',
        'Natural Language :: Panjabi',
        'Natural Language :: Persian',
        'Natural Language :: Polish',
        'Natural Language :: Portuguese',
        'Natural Language :: Portuguese (Brazilian)',
        'Natural Language :: Romanian',
        'Natural Language :: Russian',
        'Natural Language :: Serbian',
        'Natural Language :: Slovak',
        'Natural Language :: Slovenian',
        'Natural Language :: Spanish',
        'Natural Language :: Swedish',
        'Natural Language :: Tamil',
        'Natural Language :: Telugu',
        'Natural Language :: Thai',
        'Natural Language :: Turkish',
        'Natural Language :: Ukranian',
        'Natural Language :: Urdu',
        'Natural Language :: Vietnamese',
        'Operating System :: BeOS',
        'Operating System :: MacOS',
        'Operating System :: MacOS :: MacOS 9',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft',
        'Operating System :: Microsoft :: MS-DOS',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: Microsoft :: Windows :: Windows 3.1 or Earlier',
        'Operating System :: Microsoft :: Windows :: Windows 95/98/2000',
        'Operating System :: Microsoft :: Windows :: Windows CE',
        'Operating System :: Microsoft :: Windows :: Windows NT/2000',
        'Operating System :: OS/2',
        'Operating System :: OS Independent',
        'Operating System :: Other OS',
        'Operating System :: PalmOS',
        'Operating System :: PDA Systems',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: AIX',
        'Operating System :: POSIX :: BSD',
        'Operating System :: POSIX :: BSD :: BSD/OS',
        'Operating System :: POSIX :: BSD :: FreeBSD',
        'Operating System :: POSIX :: BSD :: NetBSD',
        'Operating System :: POSIX :: BSD :: OpenBSD',
        'Operating System :: POSIX :: GNU Hurd',
        'Operating System :: POSIX :: HP-UX',
        'Operating System :: POSIX :: IRIX',
        'Operating System :: POSIX :: Linux',
        'Operating System :: POSIX :: Other',
        'Operating System :: POSIX :: SCO',
        'Operating System :: POSIX :: SunOS/Solaris',
        'Operating System :: Unix',
        'Programming Language :: Ada',
        'Programming Language :: APL',
        'Programming Language :: ASP',
        'Programming Language :: Assembly',
        'Programming Language :: Awk',
        'Programming Language :: Basic',
        'Programming Language :: C',
        'Programming Language :: C#',
        'Programming Language :: C++',
        'Programming Language :: Cold Fusion',
        'Programming Language :: Cython',
        'Programming Language :: Delphi/Kylix',
        'Programming Language :: Dylan',
        'Programming Language :: Eiffel',
        'Programming Language :: Emacs-Lisp',
        'Programming Language :: Erlang',
        'Programming Language :: Euler',
        'Programming Language :: Euphoria',
        'Programming Language :: Forth',
        'Programming Language :: Fortran',
        'Programming Language :: Haskell',
        'Programming Language :: Java',
        'Programming Language :: JavaScript',
        'Programming Language :: Lisp',
        'Programming Language :: Logo',
        'Programming Language :: ML',
        'Programming Language :: Modula',
        'Programming Language :: Objective C',
        'Programming Language :: Object Pascal',
        'Programming Language :: OCaml',
        'Programming Language :: Other',
        'Programming Language :: Other Scripting Engines',
        'Programming Language :: Pascal',
        'Programming Language :: Perl',
        'Programming Language :: PHP',
        'Programming Language :: Pike',
        'Programming Language :: Pliant',
        'Programming Language :: PL/SQL',
        'Programming Language :: PROGRESS',
        'Programming Language :: Prolog',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.3',
        'Programming Language :: Python :: 2.4',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: REBOL',
        'Programming Language :: Rexx',
        'Programming Language :: Ruby',
        'Programming Language :: Scheme',
        'Programming Language :: Simula',
        'Programming Language :: Smalltalk',
        'Programming Language :: SQL',
        'Programming Language :: Tcl',
        'Programming Language :: Unix Shell',
        'Programming Language :: Visual Basic',
        'Programming Language :: XBasic',
        'Programming Language :: YACC',
        'Programming Language :: Zope',
        'Topic :: Adaptive Technologies',
        'Topic :: Artistic Software',
        'Topic :: Communications',
        'Topic :: Communications :: BBS',
        'Topic :: Communications :: Chat',
        'Topic :: Communications :: Chat :: AOL Instant Messenger',
        'Topic :: Communications :: Chat :: ICQ',
        'Topic :: Communications :: Chat :: Internet Relay Chat',
        'Topic :: Communications :: Chat :: Unix Talk',
        'Topic :: Communications :: Conferencing',
        'Topic :: Communications :: Email',
        'Topic :: Communications :: Email :: Address Book',
        'Topic :: Communications :: Email :: Email Clients (MUA)',
        'Topic :: Communications :: Email :: Filters',
        'Topic :: Communications :: Email :: Mailing List Servers',
        'Topic :: Communications :: Email :: Mail Transport Agents',
        'Topic :: Communications :: Email :: Post-Office',
        'Topic :: Communications :: Email :: Post-Office :: IMAP',
        'Topic :: Communications :: Email :: Post-Office :: POP3',
        'Topic :: Communications :: Fax',
        'Topic :: Communications :: FIDO',
        'Topic :: Communications :: File Sharing',
        'Topic :: Communications :: File Sharing :: Gnutella',
        'Topic :: Communications :: File Sharing :: Napster',
        'Topic :: Communications :: Ham Radio',
        'Topic :: Communications :: Internet Phone',
        'Topic :: Communications :: Telephony',
        'Topic :: Communications :: Usenet News',
        'Topic :: Database',
        'Topic :: Database :: Database Engines/Servers',
        'Topic :: Database :: Front-Ends',
        'Topic :: Desktop Environment',
        'Topic :: Desktop Environment :: File Managers',
        'Topic :: Desktop Environment :: Gnome',
        'Topic :: Desktop Environment :: GNUstep',
        'Topic :: Desktop Environment :: K Desktop Environment (KDE)',
        'Topic :: Desktop Environment :: K Desktop Environment (KDE) :: Themes',
        'Topic :: Desktop Environment :: PicoGUI',
        'Topic :: Desktop Environment :: PicoGUI :: Applications',
        'Topic :: Desktop Environment :: PicoGUI :: Themes',
        'Topic :: Desktop Environment :: Screen Savers',
        'Topic :: Desktop Environment :: Window Managers',
        'Topic :: Desktop Environment :: Window Managers :: Afterstep',
        'Topic :: Desktop Environment :: Window Managers :: Afterstep :: Themes',
        'Topic :: Desktop Environment :: Window Managers :: Applets',
        'Topic :: Desktop Environment :: Window Managers :: Blackbox',
        'Topic :: Desktop Environment :: Window Managers :: Blackbox :: Themes',
        'Topic :: Desktop Environment :: Window Managers :: CTWM',
        'Topic :: Desktop Environment :: Window Managers :: CTWM :: Themes',
        'Topic :: Desktop Environment :: Window Managers :: Enlightenment',
        'Topic :: Desktop Environment :: Window Managers :: Enlightenment :: Epplets',
        'Topic :: Desktop Environment :: Window Managers :: Enlightenment :: Themes DR15',
        'Topic :: Desktop Environment :: Window Managers :: Enlightenment :: Themes DR16',
        'Topic :: Desktop Environment :: Window Managers :: Enlightenment :: Themes DR17',
        'Topic :: Desktop Environment :: Window Managers :: Fluxbox',
        'Topic :: Desktop Environment :: Window Managers :: Fluxbox :: Themes',
        'Topic :: Desktop Environment :: Window Managers :: FVWM',
        'Topic :: Desktop Environment :: Window Managers :: FVWM :: Themes',
        'Topic :: Desktop Environment :: Window Managers :: IceWM',
        'Topic :: Desktop Environment :: Window Managers :: IceWM :: Themes',
        'Topic :: Desktop Environment :: Window Managers :: MetaCity',
        'Topic :: Desktop Environment :: Window Managers :: MetaCity :: Themes',
        'Topic :: Desktop Environment :: Window Managers :: Oroborus',
        'Topic :: Desktop Environment :: Window Managers :: Oroborus :: Themes',
        'Topic :: Desktop Environment :: Window Managers :: Sawfish',
        'Topic :: Desktop Environment :: Window Managers :: Sawfish :: Themes 0.30',
        'Topic :: Desktop Environment :: Window Managers :: Sawfish :: Themes pre-0.30',
        'Topic :: Desktop Environment :: Window Managers :: Waimea',
        'Topic :: Desktop Environment :: Window Managers :: Waimea :: Themes',
        'Topic :: Desktop Environment :: Window Managers :: Window Maker',
        'Topic :: Desktop Environment :: Window Managers :: Window Maker :: Applets',
        'Topic :: Desktop Environment :: Window Managers :: Window Maker :: Themes',
        'Topic :: Desktop Environment :: Window Managers :: XFCE',
        'Topic :: Desktop Environment :: Window Managers :: XFCE :: Themes',
        'Topic :: Documentation',
        'Topic :: Education',
        'Topic :: Education :: Computer Aided Instruction (CAI)',
        'Topic :: Education :: Testing',
        'Topic :: Games/Entertainment',
        'Topic :: Games/Entertainment :: Arcade',
        'Topic :: Games/Entertainment :: Board Games',
        'Topic :: Games/Entertainment :: First Person Shooters',
        'Topic :: Games/Entertainment :: Fortune Cookies',
        'Topic :: Games/Entertainment :: Multi-User Dungeons (MUD)',
        'Topic :: Games/Entertainment :: Puzzle Games',
        'Topic :: Games/Entertainment :: Real Time Strategy',
        'Topic :: Games/Entertainment :: Role-Playing',
        'Topic :: Games/Entertainment :: Side-Scrolling/Arcade Games',
        'Topic :: Games/Entertainment :: Simulation',
        'Topic :: Games/Entertainment :: Turn Based Strategy',
        'Topic :: Home Automation',
        'Topic :: Internet',
        'Topic :: Internet :: File Transfer Protocol (FTP)',
        'Topic :: Internet :: Finger',
        'Topic :: Internet :: Log Analysis',
        'Topic :: Internet :: Name Service (DNS)',
        'Topic :: Internet :: Proxy Servers',
        'Topic :: Internet :: WAP',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Browsers',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: Message Boards',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: News/Diary',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: Page Counters',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Internet :: WWW/HTTP :: Site Management :: Link Checking',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Server',
        'Topic :: Internet :: Z39.50',
        'Topic :: Multimedia',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Multimedia :: Graphics :: 3D Modeling',
        'Topic :: Multimedia :: Graphics :: 3D Rendering',
        'Topic :: Multimedia :: Graphics :: Capture',
        'Topic :: Multimedia :: Graphics :: Capture :: Digital Camera',
        'Topic :: Multimedia :: Graphics :: Capture :: Scanners',
        'Topic :: Multimedia :: Graphics :: Capture :: Screen Capture',
        'Topic :: Multimedia :: Graphics :: Editors',
        'Topic :: Multimedia :: Graphics :: Editors :: Raster-Based',
        'Topic :: Multimedia :: Graphics :: Editors :: Vector-Based',
        'Topic :: Multimedia :: Graphics :: Graphics Conversion',
        'Topic :: Multimedia :: Graphics :: Presentation',
        'Topic :: Multimedia :: Graphics :: Viewers',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Multimedia :: Sound/Audio :: Analysis',
        'Topic :: Multimedia :: Sound/Audio :: Capture/Recording',
        'Topic :: Multimedia :: Sound/Audio :: CD Audio',
        'Topic :: Multimedia :: Sound/Audio :: CD Audio :: CD Playing',
        'Topic :: Multimedia :: Sound/Audio :: CD Audio :: CD Ripping',
        'Topic :: Multimedia :: Sound/Audio :: CD Audio :: CD Writing',
        'Topic :: Multimedia :: Sound/Audio :: Conversion',
        'Topic :: Multimedia :: Sound/Audio :: Editors',
        'Topic :: Multimedia :: Sound/Audio :: MIDI',
        'Topic :: Multimedia :: Sound/Audio :: Mixers',
        'Topic :: Multimedia :: Sound/Audio :: Players',
        'Topic :: Multimedia :: Sound/Audio :: Players :: MP3',
        'Topic :: Multimedia :: Sound/Audio :: Sound Synthesis',
        'Topic :: Multimedia :: Sound/Audio :: Speech',
        'Topic :: Multimedia :: Video',
        'Topic :: Multimedia :: Video :: Capture',
        'Topic :: Multimedia :: Video :: Conversion',
        'Topic :: Multimedia :: Video :: Display',
        'Topic :: Multimedia :: Video :: Non-Linear Editor',
        'Topic :: Office/Business',
        'Topic :: Office/Business :: Financial',
        'Topic :: Office/Business :: Financial :: Accounting',
        'Topic :: Office/Business :: Financial :: Investment',
        'Topic :: Office/Business :: Financial :: Point-Of-Sale',
        'Topic :: Office/Business :: Financial :: Spreadsheet',
        'Topic :: Office/Business :: Groupware',
        'Topic :: Office/Business :: News/Diary',
        'Topic :: Office/Business :: Office Suites',
        'Topic :: Office/Business :: Scheduling',
        'Topic :: Other/Nonlisted Topic',
        'Topic :: Printing',
        'Topic :: Religion',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Scientific/Engineering :: Atmospheric Science',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Chemistry',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Scientific/Engineering :: Human Machine Interfaces',
        'Topic :: Scientific/Engineering :: Image Recognition',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Scientific/Engineering :: Medical Science Apps.',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Security',
        'Topic :: Security :: Cryptography',
        'Topic :: Sociology',
        'Topic :: Sociology :: Genealogy',
        'Topic :: Sociology :: History',
        'Topic :: Software Development',
        'Topic :: Software Development :: Assemblers',
        'Topic :: Software Development :: Bug Tracking',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Software Development :: Compilers',
        'Topic :: Software Development :: Debuggers',
        'Topic :: Software Development :: Disassemblers',
        'Topic :: Software Development :: Documentation',
        'Topic :: Software Development :: Embedded Systems',
        'Topic :: Software Development :: Internationalization',
        'Topic :: Software Development :: Interpreters',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Java Libraries',
        'Topic :: Software Development :: Libraries :: Perl Modules',
        'Topic :: Software Development :: Libraries :: PHP Classes',
        'Topic :: Software Development :: Libraries :: Pike Modules',
        'Topic :: Software Development :: Libraries :: pygame',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Libraries :: Ruby Modules',
        'Topic :: Software Development :: Libraries :: Tcl Extensions',
        'Topic :: Software Development :: Localization',
        'Topic :: Software Development :: Object Brokering',
        'Topic :: Software Development :: Object Brokering :: CORBA',
        'Topic :: Software Development :: Pre-processors',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Testing :: Traffic Generation',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: Software Development :: Version Control',
        'Topic :: Software Development :: Version Control :: CVS',
        'Topic :: Software Development :: Version Control :: RCS',
        'Topic :: Software Development :: Version Control :: SCCS',
        'Topic :: Software Development :: Widget Sets',
        'Topic :: System',
        'Topic :: System :: Archiving',
        'Topic :: System :: Archiving :: Backup',
        'Topic :: System :: Archiving :: Compression',
        'Topic :: System :: Archiving :: Mirroring',
        'Topic :: System :: Archiving :: Packaging',
        'Topic :: System :: Benchmark',
        'Topic :: System :: Boot',
        'Topic :: System :: Boot :: Init',
        'Topic :: System :: Clustering',
        'Topic :: System :: Console Fonts',
        'Topic :: System :: Distributed Computing',
        'Topic :: System :: Emulators',
        'Topic :: System :: Filesystems',
        'Topic :: System :: Hardware',
        'Topic :: System :: Hardware :: Hardware Drivers',
        'Topic :: System :: Hardware :: Mainframes',
        'Topic :: System :: Hardware :: Symmetric Multi-processing',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Logging',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Networking',
        'Topic :: System :: Networking :: Firewalls',
        'Topic :: System :: Networking :: Monitoring',
        'Topic :: System :: Networking :: Monitoring :: Hardware Watchdog',
        'Topic :: System :: Networking :: Time Synchronization',
        'Topic :: System :: Operating System',
        'Topic :: System :: Operating System Kernels',
        'Topic :: System :: Operating System Kernels :: BSD',
        'Topic :: System :: Operating System Kernels :: GNU Hurd',
        'Topic :: System :: Operating System Kernels :: Linux',
        'Topic :: System :: Power (UPS)',
        'Topic :: System :: Recovery Tools',
        'Topic :: System :: Shells',
        'Topic :: System :: Software Distribution',
        'Topic :: System :: Systems Administration',
        'Topic :: System :: Systems Administration :: Authentication/Directory',
        'Topic :: System :: Systems Administration :: Authentication/Directory :: LDAP',
        'Topic :: System :: Systems Administration :: Authentication/Directory :: NIS',
        'Topic :: System :: System Shells',
        'Topic :: Terminals',
        'Topic :: Terminals :: Serial',
        'Topic :: Terminals :: Telnet',
        'Topic :: Terminals :: Terminal Emulators/X Terminals',
        'Topic :: Text Editors',
        'Topic :: Text Editors :: Documentation',
        'Topic :: Text Editors :: Emacs',
        'Topic :: Text Editors :: Integrated Development Environments (IDE)',
        'Topic :: Text Editors :: Text Processing',
        'Topic :: Text Editors :: Word Processors',
        'Topic :: Text Processing',
        'Topic :: Text Processing :: Filters',
        'Topic :: Text Processing :: Fonts',
        'Topic :: Text Processing :: General',
        'Topic :: Text Processing :: Indexing',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Text Processing :: Markup',
        'Topic :: Text Processing :: Markup :: HTML',
        'Topic :: Text Processing :: Markup :: LaTeX',
        'Topic :: Text Processing :: Markup :: SGML',
        'Topic :: Text Processing :: Markup :: VRML',
        'Topic :: Text Processing :: Markup :: XML',
        'Topic :: Utilities',
   ]

def askYn(question, default = None, helptext = None):
    while True:
        answer = ask(question, default, helptext, required = True)
        if answer and answer[0].lower() in 'yn':
            return(answer[0].lower())

        print '\nERROR: You must select "Y" or "N".\n'


def ask(question, default = None, helptext = None, required = True,
        lengthy = False, multiline = False):
    prompt = '%s: ' % ( question, )
    if default:
        prompt = '%s [%s]: ' % ( question, default )
        if default and len(question) + len(default) > 70:
            prompt = '%s\n    [%s]: ' % ( question, default )
    if lengthy or multiline:
        prompt += '\n   >'

    if not helptext: helptext = 'No additional help available.'
    if helptext[0] == '\n': helptext = helptext[1:]
    if helptext[-1] == '\n': helptext = helptext[:-1]

    while True:
        sys.stdout.write(prompt)
        sys.stdout.flush()

        line = sys.stdin.readline().strip()
        if line == '?':
            print '=' * 70
            print helptext
            print '=' * 70
            continue
        if default and not line: return(default)
        if not line and required:
            print '*' * 70
            print 'This value cannot be empty.'
            print '==========================='
            if helptext: print helptext
            print '*' * 70
            continue
        return(line)


def buildTroveDict(troveList):
    dict = {}
    for key in troveList:
        subDict = dict
        for subkey in key.split(' :: '):
            if not subkey in subDict: subDict[subkey] = {}
            subDict = subDict[subkey]
    return(dict)
troveDict = buildTroveDict(troveList)


class SetupClass:
    def __init__(self):
        self.config = None
        self.classifierDict = {}
        self.setupData = {}
        self.setupData['classifier'] = self.classifierDict
        self.setupData['packages'] = {}

        self.loadConfigFile()


    def lookupOption(self, key):
        if not self.config.has_option('DEFAULT', key): return(None)
        return(self.config.get('DEFAULT', key))


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

        if not valuesDifferent: return

        self.config.write(open(os.path.expanduser('~/.pygiver'), 'w'))


    def loadExistingSetup(self):
        raise NotImplementedError


    def inspectFile(self, path):
        fp = open(path, 'r')
        for line in [ fp.readline() for x in range(10) ]:
            m = re.match(r'^#!.*python((?P<major>\d)(\.\d+)?)?$', line)
            if m:
                if m.group('major') == '3':
                    self.classifierDict['Programming Language :: Python :: 3'] = 1
                else:
                    self.classifierDict['Programming Language :: Python :: 2'] = 1
        fp.close()


    def inspectDirectory(self):
        dirName = os.path.basename(os.getcwd())
        self.setupData['name'] = dirName
        m = re.match(r'(.*)-(\d.+)', dirName)
        if m:
            self.setupData['name'] = m.group(1)
            self.setupData['version'] = m.group(2)

        for root, dirs, files in os.walk('.'):
            for file in files:
                if root == '.' and file == 'setup.py': continue
                fileName = os.path.join(root, file)
                self.inspectFile(fileName)

                if file == '__init__.py':
                    trySrc = os.path.join('.', 'src')
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
              lengthy = True)
        self.setupData['author'] = ask('Author name',
              self.setupData.get('author'), helpText['author'])
        self.setupData['author_email'] = ask('Author e-mail address',
              self.setupData.get('author_email'), helpText['author_email'])
        self.setupData['url'] = ask('Project URL',
              self.setupData.get('url'), helpText['url'], required = False)

        if (askYn('Do you want to set Trove classifiers?',
                helptext = helpText['do_classifier']) == 'y'):
            self.setTroveClassifier()


    def setTroveClassifier(self):
        self.setTroveDevStatus(self.classifierDict)
        self.setTroveLicense(self.classifierDict)
        self.setTroveOther(self.classifierDict)


    def setTroveOther(self, classifierDict):
        if askYn('Do you want to set other trove identifiers', 'n',
                helpText['trove_generic']) != 'y': return

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
                    % ( key, len(trove[key]) ), 'n',
                    helpText['trove_generic']) == 'y':
                self.walkTrove(classifierDict, trovePath + [trove[key]],
                        desc + ' :: ' + key)


    def setTroveLicense(self, classifierDict):
        while True:
            license = ask('What license do you use',
                  helptext = helpText['trove_license'], required = False)
            if not license: return

            licenseWords = license.lower().split(' ')

            foundList = []
            for index in range(len(troveList)):
                troveItem = troveList[index]
                if not troveItem.startswith('License :: '): continue
                troveItem = troveItem[11:].lower()

                allMatch = True
                for word in licenseWords:
                    if not word in troveItem:
                        allMatch = False
                        break
                if allMatch: foundList.append(index)

            question = 'Matching licenses:\n\n'
            for i in xrange(1, len(foundList) + 1):
                question += '   %s) %s\n' % ( i, troveList[foundList[i - 1]] )
            question += ('\nType the number of the license you wish to use or '
                     '? to try again:')
            troveLicense = ask(question, required = False)

            if troveLicense == '?': continue
            if troveLicense == '': return
            foundIndex = foundList[int(troveLicense) - 1]
            classifierDict[troveList[foundIndex]] = 1
            try:
                return
            except IndexError:
                print("ERROR: Invalid selection, type a number from the list "
                    "above.")


    def setTroveDevStatus(self, classifierDict):
        while True:
            devStatus = ask('''Please select the project status:

1 - Planning
2 - Pre-Alpha
3 - Alpha
4 - Beta
5 - Production/Stable
6 - Mature
7 - Inactive

Status''', required = False)
            if devStatus:
                try:
                    key = {
                           '1' : 'Development Status :: 1 - Planning',
                           '2' : 'Development Status :: 2 - Pre-Alpha',
                           '3' : 'Development Status :: 3 - Alpha',
                           '4' : 'Development Status :: 4 - Beta',
                           '5' : 'Development Status :: 5 - Production/Stable',
                           '6' : 'Development Status :: 6 - Mature',
                           '7' : 'Development Status :: 7 - Inactive',
                           }[devStatus]
                    classifierDict[key] = 1
                    return
                except KeyError:
                    print("ERROR: Invalid selection, type a single digit "
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
        if os.path.exists('setup.py'): shutil.move('setup.py', 'setup.py.old')

        fp = open('setup.py', 'w')
        fp.write('#!/usr/bin/env python\n\n')
        fp.write('from distutils2.core import setup\n\n')

        fp.write('from sys import version\n')
        fp.write('if version < \'2.2.3\':\n')
        fp.write('    from distutils2.dist import DistributionMetadata\n')
        fp.write('    DistributionMetadata.classifier = None\n')
        fp.write('    DistributionMetadata.download_url = None\n')

        fp.write('setup(name = %s,\n' % repr(self.setupData['name']))
        fp.write('        version = %s,\n' % repr(self.setupData['version']))
        fp.write('        description = %s,\n'
                % repr(self.setupData['description']))
        fp.write('        author = %s,\n' % repr(self.setupData['author']))
        fp.write('        author_email = %s,\n'
                % repr(self.setupData['author_email']))
        if self.setupData['url']:
            fp.write('        url = %s,\n' % repr(self.setupData['url']))
        if self.setupData['classifier']:
            fp.write('        classifier = [\n')
            for classifier in sorted(self.setupData['classifier'].keys()):
                fp.write('              %s,\n' % repr(classifier))
            fp.write('           ],\n')
        if self.setupData['packages']:
            fp.write('        packages = %s,\n'
                    % repr(self._dotted_packages(self.setupData['packages'])))
            fp.write('        package_dir = %s,\n'
                    % repr(self.setupData['packages']))
        fp.write('        #scripts = [\'path/to/script\']\n')

        fp.write('        )\n')
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
