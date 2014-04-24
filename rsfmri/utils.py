#!/usr/bin/python

import sys
import subprocess as sub
from multiprocessing.pool import ThreadPool

# our imports
from .settings import *

# our thread pool
task_pool = ThreadPool(processes=max_num_threads)


# run command (blocking)
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

# reset thread pool
def reset_tasks():
    global task_pool
    task_pool = ThreadPool(processes=max_num_threads)
    return task_pool

# run command in thread
def run_cmd_parallel(cmdstr):
    t = task_pool.apply_async(run_cmd, (cmdstr,))
    return t

# wait for all current threads to end
def wait_for_tasks():
    task_pool.close()
    task_pool.join()


def check_file(file_loc):
    if not os.path.isfile(file_loc):
        log.error('cannot find file: {}'.format(file_loc))
        sys.exit()

    return file_loc


##############################
# imaging specific 
##############################

# find center of gravity of nifti image
# (useful for finding snapshot positions)
def image_center_of_gravity(image):
    cmd = 'fslstats {} -C'.format(image)
    return [int(float(x)) for x in run_cmd(cmd).strip().split(' ')]


# find nonzero mean
def imagez_nonzero_mean(image):
    cmd = 'fslstats {} -M'.format(image)
    return float(run_cmd(cmd).strip())

