from distutils2.core import setup, Extension
setup(name='somedist',
      version='0.1',
      py_modules=['myowntestmodule', 'somemod'],
      ext_modules=[Extension('spam', ['spammodule.c'])],
)
