#!/bin/sh
echo -n "Running tests for Python 2.4... "
python2.4 runtests.py -q > /dev/null 2> /dev/null
if [ $? -ne 0 ];then
    echo "Failed"
    exit 1
else
    echo "Success"
fi

echo -n "Running tests for Python 2.5... "
python2.5 runtests.py -q > /dev/null 2> /dev/null
if [ $? -ne 0 ];then
    echo "Failed"
    exit 1
else
    echo "Success"
fi

echo -n "Running tests for Python 2.6... "
python2.6 runtests.py -q > /dev/null 2> /dev/null
if [ $? -ne 0 ];then
    echo "Failed"
    exit 1
else
    echo "Success"
fi

