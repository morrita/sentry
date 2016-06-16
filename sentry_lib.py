#!/usr/bin/python
# name: sentry_lib.py
# version: 0.1 
# date: June 2016

def representsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def get_num_file(filename):

    with open(filename, 'r') as f:
      firstLine = f.readline()

    firstList = firstLine.split()
    firstNum = firstList[0]

    if representsInt(firstNum):
      firstInt = int(firstNum)

    else:          # return a default of 0 if no integer value detected
        firstInt = 0

    return firstInt 

