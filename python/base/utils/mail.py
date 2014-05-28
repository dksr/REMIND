#!/usr/bin/python
import os
import sys
from email.iterators import *
from optparse import OptionParser
import time

def usage():
    '''Return a string detailing how this program is used.'''

    sProgramName = sys.argv[0]
    sUsage = '''

NAME:
    %s
SYNOPSIS:
    %s [OPTIONS]
DESCRIPTION:
    Sends an email.
    If the value to an argument is a file path and the file exists, the file will
    be read line by line and the values in the file will be used. When supplying 
    multiple email addresses as an argument, a comma should be used to separate them.
    Arguments with spaces should be encolsed in double quotes (").''' % (sProgramName, sProgramName)

    return sUsage

def getArgs():
    '''Get program arguments.
Returns a tuple of arguement details.
The 1st value is a dict of options.
The 2nd value is a list of positional arguments.'''

    getOptParser = OptionParser(usage())
    getOptParser.add_option('-b', '--body', action='store', type='string', dest='body',
        help='Body of email. All lines from file used if file path provided.')
    getOptParser.add_option('-s', '--subject', action='store', type='string', dest='subject',
        help='The subject of the email. Only first line of file used if file path provided.')
    getOptParser.add_option('-t', '--to', action='store', type='string', dest='to',
        help='Who the email is to be sent to. One email address per line if file path provided.')

    (dOpts, lPosArgs) = getOptParser.parse_args()

    if not (dOpts.to and dOpts.subject and dOpts.body and len(lPosArgs) == 0):
        getOptParser.print_help()
        sys.exit(2)

    return dOpts, lPosArgs

def checkInput(sInput):
    '''Check if input is a path to a file. If it is read the file and return the contents.
The input is returned if it is not a file path that exists.'''

    lData = []
    if os.path.exists(sInput):
        foIn = open(sInput, 'r')
        for sLine in foIn:
            lData.append(sLine.strip())
        foIn.close()
    else:
        lData.append(sInput)

    return lData

def main():
    '''Program entry point.'''

    # Store when program started.
    tArgs = getArgs()
    # Arguments.
    dOpts = tArgs[0]
    lArgs = tArgs[1]

    lTo      = checkInput(dOpts.to)
    lBody    = checkInput(dOpts.body)
    lSubject = checkInput(dOpts.subject)
    
    SENDMAIL = "/usr/sbin/sendmail" # sendmail location
    p = os.popen("%s -t" % SENDMAIL, "w")
    p.write("To: " + lTo[0] + "\n")
    p.write("Subject: " + lSubject[0] +"\n")
    p.write("\n") # blank line separating headers from body
    p.write('\n'.join(lBody))
    sts = p.close()
    if sts is not None:
        print "Sendmail exit status", sts
        
if __name__ == "__main__":
    main()
