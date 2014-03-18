#!/usr/bin/python

import sys
import subprocess as sub

# our imports
from .settings import *

def run_cmd(cmdstr):
    log.debug('COMMAND: {}'.format(cmdstr))

    # open process
    proc = sub.Popen(cmdstr,
                     shell = True,
                     executable='/bin/bash',
                     stdout = sub.PIPE,
                     stderr = sub.STDOUT)

    # push output to debug log
    for line in proc.stdout:
        log.debug('CMD OUT: {}'.format(line.strip()))

    # for now, we will just block all processes
    proc.wait()

    if proc.poll():
        log.error('command returned error: \"{}\"'.format(cmdstr))
        sys.exit()
