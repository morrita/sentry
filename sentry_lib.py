#!/usr/bin/python
# name: sentry_lib.py
# version: 0.2 
# date: July 2016


def update_file(message,filename): # append filename with message
    with open(filename,'a') as f:
        f.write(message)

def representsInt(s):
    try:
        int(s)
        return True

    except ValueError:
        return False

def get_num_file(filename):
    import os
    if os.path.isfile(filename):

        with open(filename, 'r') as f:
            firstLine = f.readline()

        firstList = firstLine.split()
        firstNum = firstList[0]

        if representsInt(firstNum):
            firstInt = int(firstNum)

        else:          # return a default of 0 if no integer value detected
            firstInt = 0

        return firstInt 


def system_shutdown(logfile,restart):
    if restart is True:
        command = "/usr/bin/sudo /sbin/shutdown -r now"

    else:
        command = "/usr/bin/sudo /sbin/shutdown -h now"

    message = "Now issuing command " + command + "\n"
    update_file (message, logfile)

    import subprocess
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
