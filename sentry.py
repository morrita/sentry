#!/usr/bin/python
# name: sentry.py
# version: 1.2
# author: Tom Morris
# date: April 2016

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText

import StringIO  # needed for capturing test images
from PIL import Image

import imaplib
import sys
import email
import time
from datetime import datetime
import subprocess
import os
from ConfigParser import SafeConfigParser

cfg_file = '/usr/local/bin/sentry/sentry.ini'
running_flag = '/tmp/sentry_running.tmp'
testcount = 0
 
def readConfigFile():
    # read variables from config file
    parser = SafeConfigParser()
    parser.read (cfg_file)

    global email_server; email_server = parser.get('EmailSetup', 'email_server')
    global email_user; email_user = parser.get('EmailSetup', 'email_user')
    global email_password; email_password = parser.get('EmailSetup', 'email_password')
    global emailSubject; emailSubject = parser.get('EmailSetup', 'emailSubject')

    global internet_gw; internet_gw = parser.get('EmailSetup', 'internet_gw')
    global nw_checks; nw_checks = parser.get('EmailSetup', 'nw_checks')
    nw_checks; nw_checks = nw_checks.split(',')

    global logdir; logdir = parser.get('PathSetup', 'logdir')
    global logfile; logfile = parser.get('PathSetup', 'logfile')
    global tmpdir; tmpdir = parser.get('PathSetup', 'tmpdir')
    global tmpfile; tmpfile = parser.get('PathSetup', 'tmpfile')
    global filepath; filepath = parser.get('PathSetup', 'filepath')
    global filenamePrefix; filenamePrefix = parser.get('PathSetup', 'filenamePrefix')

    global photo_width; photo_width = parser.getint('CameraSetup','photo_width') 
    global photo_height; photo_height = parser.getint('CameraSetup','photo_height') 
    global pct_quality; pct_quality = parser.getint('CameraSetup','pct_quality') 
    global sensitivity; sensitivity = parser.getint('CameraSetup','sensitivity') 
    global threshold; threshold = parser.getint('CameraSetup','threshold') 
    global test_width;test_width = parser.getint('CameraSetup','test_width') 
    global test_height; test_height = parser.getint('CameraSetup','test_height') 

    global loopThreshold; loopThreshold = parser.getint('GeneralSetup','loopThreshold') 
    global max_second; max_second = parser.getint('GeneralSetup','max_second') 
    global max_running_flags; max_running_flags = parser.getint('GeneralSetup','max_running_flags') 
    global use_acl; use_acl = parser.getboolean('GeneralSetup','use_acl') 
    global verbose; verbose= parser.getboolean('GeneralSetup','verbose') 
    global acl; acl = parser.get('GeneralSetup','acl') 
    acl = acl.split(',')


# Capture a small test image (for motion detection)
def captureTestImage():
    command = "raspistill -w %s -h %s -t 1 -e bmp -o -" % (test_width, test_height)
    imageData = StringIO.StringIO()
    imageData.write(subprocess.check_output(command, shell=True))
    imageData.seek(0)
    im = Image.open(imageData)
    buffer = im.load()
    imageData.close()
    global testcount; testcount += 1

    return im, buffer

def restart():
    command = "/usr/bin/sudo /sbin/shutdown -r now"
    import subprocess
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    update_file (output, logfile)

def shutdown():
    command = "/usr/bin/sudo /sbin/shutdown -h now"
    import subprocess
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    update_file (output, logfile)

def update_file(message,filename): # append filename with message
        with open(filename,'a') as f:
          f.write(message)

def representsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def checkIP(IPaddress): #return true if IP address pings OK

    with open(os.devnull, 'w') as fNull:
      response = False
      res = subprocess.call(['ping', '-q','-c', '1', IPaddress],stdout=fNull, stderr=fNull)

    if res == 0:
        response = True

    return (response)

def checkNetworks():  # return true if all network interfaces ping OK
    check = True
    for i in nw_checks:
      if not checkIP(i):
        datestr = get_date()
        update_file("Failed to contact network address %s at %s \n" % (i, datestr), logfile)
        check = False
        break

    return (check)


def networkAvailable(IPaddress): # return true if IP address responds OK 
    result = False


def accessPermitted(senderAddress):  # return true if senderAddress in ACL list
    if use_acl:			# check access control list for SenderAddress 
       check = False
       for a in acl:
          if (a == senderAddress):
             check = True
             break
    else:			# ignore ACL and return true
       check = True

    return (check)

def get_date(): # return current date and time
        time = datetime.now()
        return "%02d-%02d-%04d_%02d%02d%02d" % (time.day, time.month, time.year, time.hour, time.minute, time.second)

def sendEmail(emailTo,filename='',first_line=''):
    datestr = get_date()
    # Create the container (outer) email message
    msg = MIMEMultipart()
    msg['Subject'] = emailSubject + ' ' +  datestr
    msg['From'] = email_user
    msg['To'] = emailTo

    if first_line:
        msg.attach(MIMEText(first_line))

    if filename:
        if '.jpg' or '.bmp' in filename: 
          with open(filename,'rb') as f:
            img = MIMEImage(f.read(), name=os.path.basename(filename))
            msg.attach(img)

        else:
          with open (filename, 'r') as f:
            attachment = MIMEText(f.read())
            msg.attach(attachment)


    # Send the email via the SMTP server
    try:
       smtp = smtplib.SMTP(email_server)
       smtp.login(email_user, email_password)
       smtp.sendmail(email_user, emailTo, msg.as_string())
       update_file("email response sent to " + emailTo + " at: " + datestr + "\n", logfile)

    except smtplib.SMTPException:
       update_file("Error:unable to send email response to " + emailTo + " at: " + datestr + "\n", logfile)

def getEmailInfo(response_part):
    msg = email.message_from_string(response_part[1])
    varSubject = msg['subject']
    varFrom = msg['from']

    #remove the brackets around the sender email address
    varFrom = varFrom.replace('<', '')
    varFrom = varFrom.replace('>', '')

    # address = last element from list
    senderAddress =  varFrom.split()[-1]

    # truncate with (...) if subject length is greater than 35 characters
    if len( varSubject ) > 35:
        varSubject = varSubject[0:32] + '...'

    return (senderAddress, varSubject)


def saveImage(photo_width, photo_height):
    datestr = get_date()
    filename = filepath + "/" + filenamePrefix + "_" + str(photo_width) + "x" + str(photo_height) + "_" + datestr + ".jpg"
    subprocess.call("raspistill -mm matrix -w %d -h %d -e jpg -q %d -o %s" % (photo_width, photo_height, pct_quality, filename), shell=True)

    update_file("Captured %s at %s \n" % (filename,datestr), logfile)

    return (filename)


readConfigFile() # read all global variables from external configuration file


if len(sys.argv) == 2:
   if sys.argv[1] == '-v' or sys.argv[1] == '-V':
     verbose = True
     datestr = get_date()
     update_file("Program started in verbose mode at %s\n" % (datestr), logfile)

if os.path.isfile(running_flag): 
    datestr = get_date()
    update_file("Running flag %s detected at %s hence aborting\n" % (running_flag, datestr), logfile)

else:

    open(running_flag, 'a').close()  # create running flag file

    if checkNetworks():  # networks checked out fine

      if os.path.isfile (tmpfile):
        datestr = get_date()
        update_file("Networks checked out fine so removing temp file %s at %s \n" % (tmpfile, datestr), logfile)
        os.remove (tmpfile)

      m = imaplib.IMAP4_SSL(email_server)

      try:
        rv, data = m.login(email_user, email_password)

      except imaplib.IMAP4.error:
        datestr = get_date()
        update_file("IMAP login to %s as %s failed at %s \n" % (email_server,email_user,datestr), logfile)
        sys.exit(1)

      m.select('inbox')
      typ, data = m.search(None, "UNSEEN")
      ids = data[0]
      id_list = ids.split()

      # if any new emails have arrived
      if id_list:

        for i in id_list: # for each new email

          typ, data = m.fetch( i, '(RFC822)' )

          for response_part in data: # for each part of the email

            if isinstance(response_part, tuple):	# if the part is a tuple then read email info

             senderAddress, varSubject = getEmailInfo (response_part)

             if accessPermitted(senderAddress):
               if 'sentry:logs' in varSubject.lower(): # logfile requested
                 datestr = get_date()
                 update_file("A copy of the logfile was requested by %s at %s \n" % (senderAddress, datestr), logfile)
                 sendEmail (senderAddress,logfile,"Here is a copy of the logfile contents:\n")

               elif 'sentry:resetlogs' in varSubject.lower(): # logfile requested
                 os.remove (logfile)
                 datestr = get_date()
                 update_file("A logfile reset was requested by %s at %s \n" % (senderAddress, datestr), logfile)
                 sendEmail (senderAddress,logfile,"The logfile has been reset, here is the new logfile contents:\n")

               elif 'sentry:shutdown' in varSubject.lower(): # shutdown requested
                 datestr = get_date()
                 update_file("A shutdown was requested by %s at %s \n" % (senderAddress, datestr), logfile)
                 sendEmail (senderAddress,'',"Your request to shut down the system is being actioned...\n")

                 if os.path.isfile(running_flag):
                   os.remove(running_flag)

                 shutdown()

               elif 'sentry:restart' in varSubject.lower(): # shutdown requested
                 datestr = get_date()
                 update_file("A reboot was requested by %s at %s \n" % (senderAddress, datestr), logfile)
                 sendEmail (senderAddress,'',"Your request to reboot the system is being actioned...\n")

                 if os.path.isfile(running_flag): 
                   os.remove(running_flag)

                 restart()

               elif 'sentry:hires' in varSubject.lower(): # hi resolution photo requested
                 photo_width = 2592 
                 photo_height = 1944
                 filename = saveImage (photo_width, photo_height)
                 sendEmail (senderAddress,filename,"A high resolution photo was requested - please find the attached image:\n")
                 os.remove (filename)

               else:
                 filename = saveImage (photo_width, photo_height)
                 sendEmail (senderAddress,filename,"A standard image photo was requested - please find attached image:\n")
                 os.remove (filename)

             else:
               datestr = get_date()
               update_file("Email address %s not recognised at %s \n" % (senderAddress,datestr), logfile)

        m.logout()

      else:
          
          # Get first image
          image1, buffer1 = captureTestImage()
          current_second = datetime.now().second

          while (current_second < max_second):
 
              current_second = datetime.now().second

              # Get comparison image
              image2, buffer2 = captureTestImage()

              # Count changed pixels
      
              changedPixels = 0
              for x in xrange(0, test_width):
                  # Scan one line of image then check sensitivity for movement
                  for y in xrange(0, test_height):
                      # Check green as it's the highest quality channel
                      pixdiff = abs(buffer1[x, y][1] - buffer2[x, y][1])
                      if pixdiff > threshold:
                          changedPixels += 1

                  # Changed logic - If movement sensitivity exceeded then
                  # Save image and Exit before full image scan complete
                  if changedPixels > sensitivity:
                      filename = saveImage (photo_width, photo_height)
                      sendEmail ('tom_morris@btinternet.com',filename,'Here is the captured image:\n')
                      os.remove (filename)
                      datestr = get_date()
                      update_file("Alert! Motion was detected at %s \n" % (datestr), logfile)
                      update_file("changedPixels = %s , sensitivity = %s , threshold = %s \n" % (str(changedPixels), str(sensitivity), str(threshold)), logfile)
                      changedPixels = 0
                      break

              image1 = image2
              buffer1 = buffer2

          if verbose:
            datestr = get_date()
            update_file("%s test images were captured suring this run at %s \n" % (str(testcount),datestr), logfile)
          

    else:                        # network failure detected
      datestr = get_date()
      update_file("Mailer.py did not run as a network error was detected at %s \n" % (datestr), logfile)

      if os.path.isfile (tmpfile):
        update_file("Temp file %s  was detected at %s \n" % (tmpfile, datestr), logfile)

        with open(tmpfile, 'r') as f:
          firstLine = f.readline()

        firstList = firstLine.split()
        firstNum = firstList[0]

        if representsInt(firstNum):
          firstInt = int(firstNum)
          update_file("Temp file %s  contains number  %s \n" % (tmpfile, firstInt), logfile)
          firstInt += 1

          os.remove (tmpfile)
          update_file(str(firstInt),tmpfile)

          update_file("Updated temp file %s  with number  %s \n" % (tmpfile, firstInt), logfile)

          if firstInt > loopThreshold:
            datestr = get_date()
            update_file("loopThreshold exceed so removing temp file %s and rebooting at %s \n" % (tmpfile, datestr), logfile)
            restart()

      else:
        update_file("Creating temp file %s at %s \n" % (tmpfile, datestr), logfile)
        update_file("1",tmpfile)

    os.remove (running_flag)