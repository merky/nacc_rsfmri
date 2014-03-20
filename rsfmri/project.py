#!/usr/bin/python

import os
import re
import sys
import tempfile
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from shutil import copyfile

# our files
from settings import *
from graphics import *
from utils    import run_cmd
from reports  import *

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

        # results (1st-level)
        self.dir_results  = os.path.join(self.dir_output, 'results-indiv')
        self.dir_vols     = os.path.join(self.dir_results, 'vols')
        self.dir_imgs     = os.path.join(self.dir_results,  'imgs')
        self.dir_ts       = os.path.join(self.dir_results,  'timecourse')

        # results (2nd level)
        self.dir_group    = os.path.join(self.dir_output, 'results-group')
        self.dir_grp_csv  = os.path.join(self.dir_group, 'csv')
        self.dir_grp_vols = os.path.join(self.dir_group, 'vols')
        self.dir_grp_imgs = os.path.join(self.dir_group, 'imgs')

        self.sessions = sessions
        self.label    = label

        # main report
        self.report = FCReport(label)
        self.report_summary = FCReportGroupSummary()
        self.report_seeds = FCReportGroupSeeds()

        # add report groups to main report
        self.report.add_report(self.report_summary)
        self.report.add_report(self.report_seeds)


    def setup(self):
        # user-called initiation.

        # create analysis directories
        self.init_dirs()

        # log file (stored in results dir)
        self.init_log()

        # setup sessions
        self.init_sessions()


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

            # these are all in results dir
            os.makedirs(self.dir_seeds)
            os.makedirs(self.dir_vols)
            os.makedirs(self.dir_imgs)
            os.makedirs(self.dir_ts)

            os.makedirs(self.dir_group)
            os.makedirs(self.dir_grp_csv)
            os.makedirs(self.dir_grp_imgs)
            os.makedirs(self.dir_grp_vols)
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




    def create_seed(self, name, x, y, z, radius):
        log.info('creating seed, {} @ {} {} {}'.format(name,x,y,z))

        # NOTE: I'm confused as to why I have to specify 'LPI' orientation here
        #       when the MNI standard brain is in LAS. AFNI is wacky?
        filename = os.path.join(self.dir_seeds, '%s_%dmm.nii.gz' % (name, radius,))
        cmd = '3dUndump -prefix {ofile} -xyz -orient LPI -master {std} -srad {rad} <(echo \'{x} {y} {z}\')' \
                .format(ofile = filename,
                        std   = mri_standard,
                        rad   = radius,
                        x     = x,
                        y     = y,
                        z     = z)

        run_cmd(cmd)
        self.add_seed(name, filename)

        # add coordinates to report
        self.report_seeds.add_txt(name, 'Spherical ROI created at coordinates = MNI ({},{},{}), radius = {}mm' \
                                         .format(x, y, z, radius))


    def create_seed_from_file(self, list_file, radius=None):
        # creates spherical ROIs from x,y,z coordinates in file
        #  * each line should be: name, x, y, z, radius
        #  * radius is optional

        # check if file exists
        if not os.path.isfile(list_file):
            log.error('cannot find seed coord file: {}'.format(filename))
            self.exit()

        # open the file up and loop through each row
        f = open(list_file, 'r')
        try:
            for i, entry in enumerate(f):
                fields  = entry.strip().split(',')
                if len(fields) < 4:
                    log.warning('line #{} in seed file does not contain enough information, skipping.'.format(i+1))
                    continue

                # name is first field
                n = fields[0]
                # replace spaces with underscore
                n = re.sub(' ','_',n).lower()

                # following 3 fields are coords, convert to float
                x,y,z = [float(j) for j in fields[1:4]]

                # radius is optional, so we need to check that it was specified somewhere
                if radius is None:
                    if len(fields) == 5:
                        radius = float(fields[5])
                    else:
                        log.error('When creating seed from a file, you must specify the radius in the file itself or on the command line')
                        self.exit()
                self.create_seed(n,x,y,z, radius)
        except:
            info.error('Problem import seed coordinates from file {}'.format(lsit_file))
            self.exit()
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

        # snapshot of seed
        snap_img = os.path.join(self.dir_seeds, 'seed_{}.png'.format(name))
        snapshot_overlay(mri_standard, filename, snap_img, auto_coords=True)

        # add volume information to report
        self.report_seeds.add_txt(name, 'File location: {}'.format(filename))

        # add image to report
        self.report_seeds.add_img(name, snap_img, 'Snapshot of {} seed'.format(name))


    def add_seed_from_file(list_file):
        # line format in file should be: name, file_location
        f = open(list_file)
        for entry in f:
            fields = entry.split(',')
            if len(fields) > 1:
                name,filename = fields
                self.add_seed(name, filename)


    def extract_ts_all(self):

        if len(self.seeds) == 0:
            log.error('No seeds specified to extract timecourse, my friend')
            self.exit()

        for session in self.sessions:
            for seed_name in self.seeds:
                f = self.extract_ts(session, seed_name)
                session.set_ts_file(seed_name, f)


    def extract_ts(self, session, seed_name):

        log.info('extracting timecourse signal, roi={}, session={}' \
                  .format(seed_name, session.id))

        seed_file = self.seeds[seed_name]

        # timecourse will be saved to this file
        ts_file = os.path.join(self.dir_ts, '{}_{}.1d'.format(session.id, seed_name))

        # command string
        cmd = 'fslmeants -i {bold} -m {mask} -o {output}' \
                .format(bold   = session.bold,
                        mask   = seed_file,
                        output = ts_file)
        # run!
        run_cmd(cmd)

        # return new file location
        return ts_file


    def fc_matrix_groupstats(self):
        # find mean/std across all matrices
        pearson_all = pd.Panel({s.id:s.fcmatrix() for s in self.sessions})
        pearson_mean = pearson_all.mean(axis='items')

        # output csv (mean)
        outfile = os.path.join(self.dir_grp_csv, 'fc_pearson_group_mean.csv')
        pearson_mean.to_csv(outfile)

        # output csv per seed
        for seed in self.seeds:
            # file will contain row-per-session, and columns will be target seeds
            outfile = os.path.join(self.dir_grp_csv, 'fc_pearson_{}.csv'.format(seed))
            pearson_all.major_xs(seed).T.to_csv(outfile)

        ################
        ### GRAPHICS ###
        ################

        ### heatmap ####

        # image filename
        outfile = os.path.join(self.dir_grp_imgs, 'fc_pearson_group_mean_heatmap.png')

        # remove self-correlation values (to fix scale)
        p_fix = pearson_mean.values
        p_fix[np.where(np.identity(pearson_mean.shape[0]))] = 0

        # create, save figure
        fig = heatmap(p_fix, limits=[0,np.nanmax(p_fix)], labels=pearson_mean.index)
        plt.savefig(outfile)

        # add to report
        self.report_summary.add_img(outfile, 'Heatmap of Functional Connectivity')

        ### network graph ####

        # image filename
        outfile = os.path.join(self.dir_grp_imgs, 'fc_pearson_group_mean_network.png')

        # generate network graph
        thresh = 0.1
        g = generate_network_graph(matrix = p_fix,
                                   thresh = thresh,
                                   nodes  = pearson_mean.index)
        # create, save figure
        fig = plot_network_graph(g)
        plt.savefig(outfile)

        # add to report
        self.report_summary.add_img(outfile, 'Network Graph (thresh >= {})'.format(thresh))


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
            run_cmd(cmd)

            # results
            session.set_rmap_file(seed_name, out_file)

            # normalize result map
            self.volume_r2z(session, seed_name, out_file)

            ### graphics ###
            log.info('Generating snapshot image for results, roi={}, session={}'.format(seed_name, session.id))
            snap_img = os.path.join(self.dir_imgs,
                                    '{}_{}_pearson_z_snapshot.png'.format(session.id, seed_name))
            snapshot_overlay(mri_standard, out_file, snap_img)


    def fc_voxelwise_groupstats(self):
        for seed_name in self.seeds:
            zmaps = [s.get_zmap_file(seed_name) for s in self.sessions]
            zmaps_str = ' '.join(zmaps)

            # concatenate vols to temp file
            tmp = tempfile.mktemp(suffix='.nii.gz')
            cmd = "fslmerge -t {} {}".format(tmp, zmaps_str)
            run_cmd(cmd)

            # run t-test
            log.info('running group t-test on z-maps, roi={}'.format(seed_name))
            outbase = os.path.join(self.dir_grp_vols, '{}'.format(seed_name))
            cmd = "randomise -i {} -o {} -m {} -1 -T".format(tmp, outbase, mri_brain_mask)
            run_cmd(cmd)

            # calculate mean z-map
            log.info('creating group mean z-map, roi={}'.format(seed_name))
            outfile = os.path.join(self.dir_grp_vols, '{}_z_mean.nii.gz'.format(seed_name))
            cmd = "fslmaths {} -Tmean {}".format(tmp, outfile)
            run_cmd(cmd)

            ### graphics ###
            log.info('Generating snapshot image for results, roi={}'.format(seed_name))
            snap_img = os.path.join(self.dir_grp_imgs,
                                    '{}_pearson_z_snapshot.png'.format(seed_name))
            snapshot_overlay(mri_standard, outfile, snap_img)

            # add to report
            self.report_seeds.add_img(seed_name, snap_img,
                                      'Group mean functional connectivity with {} (z(r) > 0.1)'.format(seed_name))


    def generate_report(self):

        # write to file
        log.info('Generating report...')
        report_file = os.path.join(self.dir_group, 'report.html')
        self.report.render_to_file(report_file)

        log.info('*********************************************')
        log.info('* report: {}'.format(report_file))
        log.info('*********************************************')


    def volume_r2z(self, session, seed_name, infile):
        log.info('converting r-map to z-map, roi={}, session={}'.format(seed_name, session.id))
        outfile = re.sub('.nii.gz$', '_z.nii.gz', infile)

        cmd = "3dcalc -a {input} -expr 'log((1+a)/(1-a))/2' -prefix {output}" \
               .format(input = infile, output = outfile)

        run_cmd(cmd)

        session.set_zmap_file(seed_name, outfile)


    def exit(self):
        # TODO: clean up anything?
        sys.exit()
