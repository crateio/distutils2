EZ = bin/easy_install
VIRTUALENV = virtualenv
PYTHON = bin/python
HG = hg
NOSE = bin/nosetests --with-xunit -s
TESTS = distutils2/tests

.PHONY: release build

build:
	$(VIRTUALENV) --no-site-packages --distribute .
	$(PYTHON) setup.py build

release:
	hg tag -f `python setup.py --version`
	cd docs; make html
	$(PYTHON) -m distutils2.run upload_docs
	$(PYTHON) setup.py register sdist upload

test:
	$(NOSE) $(TESTS)
