#!/bin/sh
echo -n "Running tests for Python 2.4... "
rm -f distutils2/_backport/_hashlib.so
python2.4 setup.py build_ext -f -q 2> /dev/null > /dev/null
python2.4 -Wd runtests.py -q 2> /dev/null
if [ $? -ne 0 ];then
    echo Failed
    rm -f distutils2/_backport/_hashlib.so
    exit 1
else
    echo Success
fi

echo -n "Running tests for Python 2.5... "
python2.5 -Wd runtests.py -q 2> /dev/null
if [ $? -ne 0 ];then
    echo Failed
    exit 1
else
    echo Success
fi

echo -n "Running tests for Python 2.6... "
python2.6 -Wd runtests.py -q 2> /dev/null
if [ $? -ne 0 ];then
    echo Failed
    exit 1
else
    echo Success
fi

echo -n "Running tests for Python 2.7... "
python2.7 -Wd -bb -3 runtests.py -q 2> /dev/null
if [ $? -ne 0 ];then
    echo Failed
    exit 1
else
    echo Success
fi

LIB=$( python3.1 -c "from distutils.util import get_platform; import sys; print('lib.%s-%s' % (get_platform(), sys.version[0:3]))" )


echo -n "Running tests for Python 3.1... "
python3.1 setup.py build -q 2> /dev/null > /dev/null
cp runtests.py build/
cd build
PYTHONPATH=${LIB} python3.1 runtests.py -q 2> /dev/null 

if [ $? -ne 0 ];then
    echo Failed
    exit 1
else
    echo Success
fi

echo -n "Running tests for Python 3.2... "
python3.2 setup.py build -q 2> /dev/null > /dev/null
cp runtests.py build/
cd build
PYTHONPATH=${LIB} python3.2 runtests.py -q 2> /dev/null

if [ $? -ne 0 ];then
    echo Failed
    exit 1
else
    echo Success
fi

echo -n "Running tests for Python 3.3... "
python3.2 setup.py build -q 2> /dev/null > /dev/null
cp runtests.py build/
cd build
PYTHONPATH=${LIB} python3.3 runtests.py -q 2> /dev/null

if [ $? -ne 0 ];then
    echo Failed
    exit 1
else
    echo Success
fi
echo "Good job, commit now! (or add tests)"
