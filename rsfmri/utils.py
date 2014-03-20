#!/usr/bin/python

import sys
import subprocess as sub
from multiprocessing.pool import ThreadPool

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

    # for now, we will just block all processes
    stdout,_ = proc.communicate()

    # push output to debug log
    for line in stdout.split('\n'):
        log.debug('CMD OUT: {}'.format(line.strip()))

    if proc.poll():
        log.error('command returned error: \"{}\"'.format(cmdstr))
        sys.exit()

    # return stdout string
    return stdout


pool = ThreadPool()
def run_cmd_parallel(cmdstr):
    t = pool.apply_async(run_cmd, (cmdstr,))
    return t

