#!/usr/bin/python

import sys
import subprocess
import fcntl
import time
import os
import stat

if __name__ == '__main__' :
  lockfile = sys.argv[1]
  contfile = sys.argv[2]
  command = ' '.join(sys.argv[3:])
  
  # Create writeable file
  flags = os.O_WRONLY | os.O_CREAT 

  # User, group, and others have read/write permission
  mode = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH 
  
  # Prevents always downgrading umask to 0
  umask = 0o777 ^ mode

  # Open file descriptor
  umask_original = os.umask(umask)
  try:
    fdesc = os.open(lockfile, flags, mode)
  finally:
    os.umask(umask_original)

  with os.fdopen(fdesc, 'w') as lf :
    print('Acquiring lock "%s" for "%s"' % (lockfile, command))

    fcntl.flock(lf, fcntl.LOCK_EX)
    
    print('Running "%s"' % command)

    # Write empty file to show when the process continues after acquiring lock
    f = open(contfile,'w')
    f.write('%f' % time.time())
    f.close()

    print subprocess.check_output(command,stderr=subprocess.STDOUT,shell=True)

    print('Releasing lock "%s"' % lockfile)

    fcntl.flock(lf, fcntl.LOCK_UN)

