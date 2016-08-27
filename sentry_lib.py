#!/usr/bin/python
# name: sentry_lib.py
# version: 0.3 
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


def dropbox_upload(verbose,logfile,appname,token,uploadfile):
    
  if verbose:
    message = "INFO: using appname = " + appname + " to upload to Dropbox\n"
    update_file (message, logfile)

  import dropbox
  import os.path
  from dropbox.exceptions import ApiError, AuthError
  from dropbox.files import WriteMode

  dbx = dropbox.Dropbox(token)

  try:
    dbx.users_get_current_account()
    if os.path.isfile(uploadfile):
      with open(uploadfile, 'rb') as f:

        filename = '/' + os.path.basename(uploadfile)

        try:
            dbx.files_upload(f, filename, dropbox.files.WriteMode.overwrite)
            if verbose:
               message = "INFO: successfully uploaded file " + uploadfile + " as " + filename + " to Dropbox within application " + appname + " \n"
               update_file (message, logfile)

        except ApiError as err:
          message = "ERROR: an error ocurred attemping to upload file to dropbox\n"
          update_file (message, logfile)

    else:
      message = "ERROR: filename " + uploadfile + " does not exist hence not uploading to Dropbox\n"
      update_file (message, logfile)

  except AuthError as err:
    message = "ERROR: Invalid Dropbox access token\n"
    update_file (message, logfile)
