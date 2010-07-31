#!/bin/sh
echo -n "Running tests for Python 2.4... "
rm -rf *.so
python2.4 setup.py build_ext -i -q 2> /dev/null > /dev/null
python2.4 -Wd runtests.py -q 2> /dev/null
rm -rf *.so
if [ $? -ne 0 ];then
    echo "Failed"
    exit 1
else
    echo "Success"
fi

echo -n "Running tests for Python 2.5... "
python2.5 setup.py build_ext -i -q 2> /dev/null > /dev/null
python2.5 -Wd runtests.py -q 2> /dev/null
rm -rf *.so
if [ $? -ne 0 ];then
    echo "Failed"
    exit 1
else
    echo "Success"
fi

echo -n "Running tests for Python 2.6... "
python2.6 -Wd runtests.py -q 2> /dev/null
if [ $? -ne 0 ];then
    echo "Failed"
    exit 1
else
    echo "Success"
fi

echo -n "Running tests for Python 2.7... "
python2.7 -Wd -bb -3 runtests.py -q 2> /dev/null
if [ $? -ne 0 ];then
    echo "Failed"
    exit 1
else
    echo "Success"
fi
