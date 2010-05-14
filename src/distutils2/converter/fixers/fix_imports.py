"""distutils2.converter.fixers.fix_imports

Fixer for import statements in setup.py
"""
from lib2to3.fixer_base import BaseFix
from lib2to3.fixer_util import syms


class FixImports(BaseFix):
    """Makes sure all import in setup.py are translated"""

    PATTERN = """
    import_from< 'from' imp=any 'import' ['('] any [')'] >
    |
    import_name< 'import' imp=any >
    """

    def transform(self, node, results):
        imp = results['imp']
        if node.type != syms.import_from:
            return

        while not hasattr(imp, 'value'):
            imp = imp.children[0]

        if imp.value == 'distutils':
            imp.value = 'distutils2'
            imp.changed()
            return node

        if imp.value == 'setuptools':
            # catching "from setuptools import setup"
            pattern = []
            next = imp.get_next_sibling()
            while next is not None:
                pattern.append(next.value)
                next = next.get_next_sibling()
            if pattern == ['import', 'setup']:
                imp.value = 'distutils2.core'
                imp.changed()

            return node
