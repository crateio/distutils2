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
	hg tag `python setup.py --version`
	hg ci -m "Release tagged"
	cd docs; make html
	$(PYTHON) setup.py upload_docs
	$(PYTHON) setup.py register sdist upload

test:
	$(NOSE) $(TESTS)
