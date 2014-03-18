#!/usr/bin/python

import os
import re
import sys
import tempfile
import numpy as np
import pandas as pd
import subprocess as sub
import matplotlib.pyplot as plt
from shutil import copyfile

# our files
from settings import *

##########################
# functional connectivity
##########################

class FCProject(object):
    seeds = {}
    results = {}

    def __init__(self, label, output_dir, input_dir, sessions):
        # define directories
        self.dir_input    = os.path.abspath(input_dir)
        self.dir_output   = os.path.join(os.path.abspath(output_dir), label)
        self.dir_seeds    = os.path.join(self.dir_output, 'seeds')
        self.dir_sessions = os.path.join(self.dir_output, 'sessions')
        self.dir_results  = os.path.join(self.dir_output, 'results')
        self.dir_vols     = os.path.join(self.dir_output, 'results','volumes')
        self.dir_mats     = os.path.join(self.dir_output, 'results','matrices')
        self.dir_imgs     = os.path.join(self.dir_output, 'results','imgs')
        self.dir_ts       = os.path.join(self.dir_output, 'results','timecourse')
        self.dir_group    = os.path.join(self.dir_output, 'results','group-stats')

        self.sessions = sessions
        self.label    = label


    def setup(self):
        # user-called initiation.

        # create analysis directories
        self.init_dirs()

        # log file (stored in results dir)
        self.init_log()

        # setup sessions
        self.init_sessions()

        # TODO: copy over existing seed files into results dir


    def init_dirs(self): # create directories
        try:
            os.makedirs(self.dir_output)
        except OSError, e:
            if e.errno ==17:
                log.error('Results directory already exists: %s', self.dir_output)
            else:
                log.error('Could not create results directory: %s', self.dir_output)
            self.exit()

        try:
            # create child dirs in output dir
            os.makedirs(self.dir_results)
            os.makedirs(self.dir_sessions)
            os.makedirs(self.dir_group)

            # these are all in results dir
            os.makedirs(self.dir_seeds)
            os.makedirs(self.dir_vols)
            os.makedirs(self.dir_mats)
            os.makedirs(self.dir_imgs)
            os.makedirs(self.dir_ts)
        except:
            # if they already exist, big woop!
            pass


    def init_log(self, log_level=logging.DEBUG):
        # log file
        self.log_file = os.path.join(self.dir_output, log_filebase)
        log_handler  = logging.FileHandler(self.log_file)
        log_handler.setLevel(log_level)

        # log format
        log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        log_handler.setFormatter(log_format)

        # add log handlers
        log.addHandler(log_handler)


    def init_sessions(self):
        # create session file
        f = open(os.path.join(self.dir_output, 'sessions.lst'), 'w')

        for session in self.sessions:
            # soft-links to input session directory
            os.symlink(os.path.join(self.dir_input, session.id),
                       os.path.join(self.dir_sessions, session.id))
            # write session id to file
            f.write('{}{}'.format(session.id, os.linesep))

        f.close()


    def run(self, cmdstr):
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
            self.exit()


    def create_seed(self, name, x, y, z, radius):
        log.info('creating seed, {} @ {} {} {}'.format(name,x,y,z))

        # TODO: I'm confused as to why I have to specify 'LPI' orientation here
        #       when the MNI standard brain is in LAS. AFNI is wacky?
        filename = os.path.join(self.dir_seeds, '%s_%dmm.nii.gz' % (name, radius,))
        cmd = '3dUndump -prefix {ofile} -xyz -orient LPI -master {std} -srad {rad} <(echo \'{x} {y} {z}\')' \
                .format(ofile = filename,
                        std   = mri_standard,
                        rad   = radius,
                        x     = x,
                        y     = y,
                        z     = z)

        self.run(cmd)
        self.add_seed(name, filename)


    def create_seed_from_file(self, list_file, radius=None):
        # line format in file should be: name, x, y, z, [radius]
        # where radius is optional
        f = open(list_file, 'r')
        try:
            for i, entry in enumerate(f):
                fields  = entry.strip().split(',')
                if len(fields) < 4:
                    log.warning('line #{} in seed file does not contain enough information, skipping.'.format(i+1))
                    continue

                n,x,y,z = fields[0:4]

                # radius is optional, so we need to check that it was specified somewhere
                if radius is None:
                    if len(fields) == 5:
                        radius = fields[5]
                    else:
                        log.error('When creating seed from a file, you must specify the radius in the file itself or on the command line')
                        self.exit()
                self.create_seed(n,x,y,z, radius)
        finally:
            f.close()


    def add_seed(self, name, filename):
        if not os.path.isfile(filename):
            log.error('cannot find seed file: {}'.format(filename))
            self.exit()

        # copy seed file over to project, if needed
        seedfile = os.path.join(self.dir_seeds, os.path.basename(filename))
        if seedfile != filename:
            log.info('copying seed file into project: {}'.format(filename))
            copyfile(filename, seedfile)

        self.seeds[name] = seedfile


    def add_seed_from_file(list_file):
        # line format in file should be: name, file_location
        f = open(list_file)
        for entry in f:
            fields = entry.split(',')
            if len(fields) > 1:
                name,filename = fields
                self.add_seed(name, filename)


    def extract_ts_all(self):
        for session in self.sessions:
            self.extract_ts(session)


    def extract_ts(self, session):
        if len(self.seeds) == 0:
            log.error('No seeds specified to extract timecourse, my friend')
            self.exit()

        for seed_name, seed_file in self.seeds.iteritems():
            log.info('extracting timecourse signal, roi={}, session={}' \
                      .format(seed_name, session.id))

            # timecourse will be saved to this file
            ts_file = os.path.join(self.dir_ts, '{}_{}.1d'.format(session.id, seed_name))

            # command string
            cmd = 'fslmeants -i {bold} -m {mask} -o {output}' \
                    .format(bold   = session.bold,
                            mask   = seed_file,
                            output = ts_file)

            self.run(cmd)

            # track files
            session.set_ts_file(seed_name, ts_file)


    def fc_matrix_groupstats(self):
        # find mean/std across all matrices
        pearson_all = pd.Panel({s.id:s.fcmatrix() for s in self.sessions})
        pearson_mean = pearson_all.mean(axis='items')
        #pearson_std  = pearson_all.stdev(axis='items')

        # TODO: run t-test
        # TODO: output heatmap graphic
        # TODO: html summary???

        # output csv (mean)
        outfile = os.path.join(self.dir_group, 'fc_pearson_group_mean.csv')
        pearson_mean.to_csv(outfile)

        # output heatmap
        # TODO: work on heatmap output (looks horrible; needs labels)
        outfile = os.path.join(self.dir_imgs, 'fc_pearson_group_mean.png')
        fig = plt.pcolor(pearson_mean)
        plt.title('Pearson corr. coeff. between ROIs')
        plt.colorbar()
        plt.savefig(outfile)

        # output csv per seed
        for seed in self.seeds:
            # file will contain row-per-session, and columns will be target seeds
            outfile = os.path.join(self.dir_group, 'fc_pearson_{}.csv'.format(seed))
            pearson_all.major_xs(seed).T.to_csv(outfile)


    def fc_voxelwise_all(self):
        for session in self.sessions:
            self.fc_voxelwise(session)


    def fc_voxelwise(self, session):
        for seed_name in self.seeds:
            log.info('running voxel-wise correlation, roi={}, session={}' \
                      .format(seed_name, session.id))

            # timecourse file
            ts_file = session.get_ts_file(seed_name)

            # output volume
            out_file = os.path.join(self.dir_vols,
                                    '{}_{}_pearson.nii.gz'.format(session.id, seed_name))

            cmd = "3dTcorr1D -pearson -prefix {output} -mask {mask} {file3d} {ts}" \
                      .format(output = out_file,
                              mask   = mri_brain_mask,
                              file3d = session.bold,
                              ts     = ts_file)
            # run
            self.run(cmd)

            # results
            session.set_rmap_file(seed_name, out_file)

            # normalize result map
            self.volume_r2z(session, seed_name, out_file)


    def fc_voxelwise_groupstats(self):
        for seed_name in self.seeds:
            zmaps = [s.get_zmap_file(seed_name) for s in self.sessions]
            zmaps_str = ' '.join(zmaps)

            # concatenate vols to temp file
            tmp = tempfile.mktemp(suffix='.nii.gz')
            cmd = "fslmerge -t {} {}".format(tmp, zmaps_str)
            self.run(cmd)

            # run t-test
            log.info('running group t-test on z-maps, roi={}'.format(seed_name))
            outbase = os.path.join(self.dir_group, '{}'.format(seed_name))
            cmd = "randomise -i {} -o {} -m {} -1 -T".format(tmp, outbase, mri_brain_mask)
            self.run(cmd)

            # calculate mean z-map
            log.info('creating group mean z-map, roi={}'.format(seed_name))
            outfile = os.path.join(self.dir_group, '{}_z_mean.nii.gz'.format(seed_name))
            cmd = "fslmaths {} -Tmean {}".format(tmp, outfile)
            self.run(cmd)


    def volume_r2z(self, session, seed_name, infile):
        log.info('converting r-map to z-map, roi={}, session={}'.format(seed_name, session.id))

        outfile = re.sub('.nii.gz$', '_z.nii.gz', infile)

        cmd = "3dcalc -a {input} -expr 'log((1+a)/(1-a))/2' -prefix {output}" \
               .format(input = infile, output = outfile)

        self.run(cmd)

        session.set_zmap_file(seed_name, outfile)


    def exit(self):
        # TODO: clean up anything?
        sys.exit()
