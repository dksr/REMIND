import os
import subprocess

# Create a long command line
ppserver_cmd = "python " + \
               "/home/csunix/visdata/cofriend/ext_lib/lib/python2.5/site-packages/ppserver.py " + \
               "-p 8080 " + \
               "-t 32"

# Call the subprocess using convenience method
pid = os.fork()
if not pid:
    retval = subprocess.call(ppserver_cmd, shell=True)
    print 'now ppserver killed'
    os._exit(0)

print 'ppserver started'

