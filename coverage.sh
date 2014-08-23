#!/bin/bash

. env/bin/activate

which coverage >/dev/null 2>&1
if [ "$?" -ne 0 ]; then
  pip install coverage
fi

coverage run manage.py test
coverage report
