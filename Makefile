EZ = bin/easy_install
VIRTUALENV = virtualenv
PYTHON = bin/python
HG = hg

.PHONY: release build

build:
	$(VIRTUALENV) --no-site-packages --distribute .
	$(PYTHON) setup.py build

release:
	hg tag `python setup.py --version`
	cd docs; make html
	$(PYTHON) setup.py upload_docs
	$(PYTHON) setup.py register sdist upload
