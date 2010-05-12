"""Fixer for setup() options.

All distutils or setuptools options are translated
into PEP 345-style options.
"""

# Local imports
from lib2to3 import pytree
from lib2to3.pgen2 import token
from lib2to3 import fixer_base
from lib2to3.fixer_util import Assign, Name, Newline, Number, Subscript, syms

# XXX where is that defined ?
_ARGLIST = 259
_ARG = 260

# name mapping : we want to convert
# all old-style options to distutils2 style
_OLD_NAMES = {'url': 'home_page',
              'long_description': 'description',
              'description': 'summary'}

class FixSetupOptions(fixer_base.BaseFix):

    # XXX need to find something better here :
    # identify a setup call, whatever alias is used
    PATTERN = """
            power< name='setup' trailer< '(' [any] ')' > any* >
              """

    def _fix_name(self, node):
        for child in node.children:
            if child.type != token.NAME:
                self._fix_name(child)
            else:
                # let's see if it's a left operator
                sibling = child.get_next_sibling()
                if sibling is None or sibling.type != token.EQUAL:
                    # nope
                    return
                if child.value in _OLD_NAMES:
                    child.value = _OLD_NAMES[child.value]
                    child.changed()

    def transform(self, node, results):
        trailer = node.children[1]
        self._fix_name(trailer)
        return node

