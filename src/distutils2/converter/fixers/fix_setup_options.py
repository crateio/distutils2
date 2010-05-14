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
              'description': 'summary',
              'install_requires': 'requires_dist'}

# XXX see what we want to do for these..
_INCOMPATIBLE_OPTIONS = ['entry_points',
                         'include_package_data',
                         'zip_safe',
                         'namespace_packages']

class FixSetupOptions(fixer_base.BaseFix):

    # XXX need to find something better here :
    # identify a setup call, whatever alias is used
    PATTERN = """
            power< name='setup' trailer< '(' [any] ')' > any* >
              """

    def _fix_name(self, argument, remove_list):
        name = argument.children[0]
        sibling = name.get_next_sibling()
        if sibling is None or sibling.type != token.EQUAL:
            return False

        if name.value in _OLD_NAMES:
            name.value = _OLD_NAMES[name.value]
        elif name.value in _INCOMPATIBLE_OPTIONS:
            # removing the args, and the comma
            # behind
            next_token = name.parent.get_next_sibling()
            if next_token.type == 12:
                remove_list.append(next_token)
            remove_list.append(name.parent)
        return True

    def transform(self, node, results):
        arglist = node.children[1].children[1]
        remove_list = []
        changed = False

        for subnode in arglist.children:
            if subnode.type != _ARG:
                continue
            if self._fix_name(subnode, remove_list) and not changed:
                changed = True

        for subnode in remove_list:
            subnode.remove()

        if changed:
            node.changed()
        return node

