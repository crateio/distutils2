#!/bin/sh
echo Testing with Python 2.4....
python2.4 runtests.py -q

echo
echo Testing with Python 2.5....
python2.5 runtests.py -q

echo
echo Testing with Python 2.6....
python2.6 runtests.py -q

