#!/usr/bin/python

import sys, os
import subprocess as sub
from multiprocessing.pool import ThreadPool
from multiprocessing import cpu_count

# our imports
from .settings import *


# number of threads is socket * cores
def calc_num_threads():
    try:
        # get number of cpus (ignore hyperthreading... just 'cus)
        cmd = 'lscpu | grep -e Socket -e Core | cut -d: -f2'
        cpu_info = [int(x.strip()) for x in os.popen(cmd).readlines()]
        cpu_num  = reduce(lambda x,y: x*y, cpu_info)

        # get current number of "active" threads
        cmd = 'cat /proc/loadavg | awk \'{print $4}\' | cut -d/ -f1'
        thread_count = int(os.popen(cmd).readlines()[0])

        # mostly use active threads to guide our decision
        cpu_approx_free = cpu_num - thread_count

        use_threads = max([cpu_approx_free, 1])

    except:
        use_threads = max([cpu_count()/2, 1])

    return use_threads


# our thread pool
def get_task_pool():
    return ThreadPool(processes=calc_num_threads())


task_pool = get_task_pool()


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
    task_pool = get_task_pool()
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

