#!/bin/sh
echo -n "Running tests with Python 2.4... "
python2.4 setup.py build_ext -f -q 2> /dev/null > /dev/null
python2.4 -Wd runtests.py -q
if [ $? -ne 0 ];then
    echo Failed, re-running
    python2.4 -Wd runtests.py
    exit 1
else
    echo Success
fi

echo -n "Running tests with Python 2.5... "
python2.5 -Wd runtests.py -q
if [ $? -ne 0 ];then
    echo Failed, re-running
    python2.5 -Wd runtests.py
    exit 1
else
    echo Success
fi

echo -n "Running tests with Python 2.6... "
python2.6 -Wd runtests.py -q
if [ $? -ne 0 ];then
    echo Failed, re-running
    python2.6 -Wd runtests.py
    exit 1
else
    echo Success
fi

echo -n "Running tests with Python 2.7... "
python2.7 -Wd -bb -3 runtests.py -q
if [ $? -ne 0 ];then
    echo Failed, re-running
    python2.7 -Wd -bb -3 runtests.py
    exit 1
else
    echo Success
fi

if [ $? -ne 0 ];then
    echo Failed
    exit 1
else
    echo "Good job, commit now! (or add tests)"
fi
