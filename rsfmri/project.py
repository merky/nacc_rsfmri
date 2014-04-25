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
from seed     import FCSeed, create_seeds_from_file
from graphics import heatmap, generate_network_graph, \
                     plot_network_graph, snapshot_overlay
from utils    import run_cmd, reset_tasks, run_cmd_parallel, \
                     wait_for_tasks, check_file, imagez_nonzero_mean
from reports  import *


#########################################
# 1st-level analysis
#########################################

class FCSeedAnalysis(object):
    def __init__(self, project, session, seed):
        self.project   = project
        self.session   = session
        self.seed      = seed

        # ts
        fname = '{}_{}.1d'.format(self.session.id, self.seed.name)
        self.file_ts = os.path.join(self.project.dir_ts, fname)

        # rmap
        fname = '{}_{}_pearson.nii.gz'.format(self.session.id, self.seed.name)
        self.file_rmap = os.path.join(self.project.dir_vols, fname)

        # zmap
        fname = '{}_{}_pearson_z.nii.gz'.format(self.session.id, self.seed.name)
        self.file_zmap = os.path.join(self.project.dir_vols, fname)

        # zmap snapshot
        fname = '{}_{}_pearson_z_snapshot.png'.format(session.id, self.seed.name)
        self.file_zmap_snapshot = os.path.join(self.project.dir_imgs, fname)

        # add self to session
        self.session.add_stats(self)

    def extract_ts(self):
        self.debug('Extracting timecourse signal')

        # command string
        cmd = 'fslmeants -i {bold} -m {mask} -o {output}' \
                .format(bold   = self.session.bold,
                        mask   = self.seed.file,
                        output = self.file_ts)

        # returns threadpool.apply_async object
        return run_cmd_parallel(cmd)

    def fc_voxelwise(self):
        self.debug('Computing connectivity map')

        # command string
        cmd = "3dTcorr1D -pearson -prefix {output} -mask {mask} {file3d} {ts}" \
                  .format(output = self.file_rmap,
                          mask   = mri_brain_mask,
                          file3d = self.session.bold,
                          ts     = self.file_ts)

        return run_cmd_parallel(cmd)

    def fc_voxelwise_fisherz(self):
        self.debug('Converting R to z map')

        # command string
        cmd = "3dcalc -a {input} -expr 'log((1+a)/(1-a))/2' -prefix {output}" \
               .format(input=self.file_rmap, output=self.file_zmap)

        return run_cmd_parallel(cmd)

    def snapshot_z(self):
        self.debug('Taking snapshot image of z map')

        snapshot_overlay(mri_standard, self.file_zmap, self.file_zmap_snapshot)

    def run(self):
        # This runs all steps (blocking)
        #self.extract_ts()
        #self.fc_voxelwise()
        #self.fc_voxelwise_fisherz()
        #self.snapshot_z()
        pass

    def debug(self, statement):
        log.debug('SESSION={}, SEED={}, {}'.format(self.session.id, self.seed.name, statement))



#########################################
# functional connectivity project
#########################################

class FCProject(object):
    def __init__(self, label, output_dir, input_dir, sessions):
        # define directories
        self.dir_input    = os.path.abspath(input_dir)
        self.dir_output   = os.path.join(os.path.abspath(output_dir), label)
        self.dir_seeds    = os.path.join(self.dir_output, 'seeds')
        self.dir_sessions = os.path.join(self.dir_output, 'sessions')

        # results (1st-level)
        self.dir_results  = os.path.join(self.dir_output,  'results-indiv')
        self.dir_vols     = os.path.join(self.dir_results, 'vols')
        self.dir_imgs     = os.path.join(self.dir_results, 'imgs')
        self.dir_ts       = os.path.join(self.dir_results, 'timecourse')

        # results (2nd level)
        self.dir_group    = os.path.join(self.dir_output, 'results-group')
        self.dir_grp_csv  = os.path.join(self.dir_group,  'csv')
        self.dir_grp_vols = os.path.join(self.dir_group,  'vols')
        self.dir_grp_imgs = os.path.join(self.dir_group,  'imgs')

        # inside /vols
        self.dir_grp_vols_mean  = os.path.join(self.dir_grp_vols,  'zmean')
        self.dir_grp_vols_ttest = os.path.join(self.dir_grp_vols,  'ttest')

        # initialize
        self.sessions = sessions
        self.label    = label
        self.seeds = []
        self.seed_stats = []

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

            # inside results-group/vols
            os.makedirs(self.dir_grp_vols_mean)
            os.makedirs(self.dir_grp_vols_ttest)
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


    def add_seed(self, seed):
        self.seeds.append(seed)

        log.info('Adding seed {} to project...'.format(seed.name))

        # check to see if roi has useful data
        if imagez_nonzero_mean(seed.file) <= 0:
            log.error('Seed volume does not contain any values > 1')
            self.exit()

        # create analysis procedures for seed
        for session in self.sessions:
            self.seed_stats.append( FCSeedAnalysis(self, session, seed) )

        # report (snapshots of seed volume)
        snap_img = os.path.join(self.dir_seeds,
                                '{}_snapshot.png'.format(seed.name))
        # produce image
        snapshot_overlay(mri_standard, seed.file, snap_img, vmin=.5, vmax=1.2, auto_coords=True)

        # add image to report
        self.report_seeds.add_img(seed.name, snap_img,
                                  'Seed volume, file={}'.format(seed.file))


    def create_seeds_from_file(self, list_file, radius=None):
        seeds = create_seeds_from_file(self.dir_seeds, list_file, radius)
        for seed in seeds: self.add_seed(seed)

    def add_seeds_from_file(self, list_file):
        # line format in file should be: name, file_location
        log.info('Importing seed volumes from file: {}'.format(list_file))
        f = open(check_file(list_file), 'r')
        try:
            for entry in f:
                fields = entry.strip().split(',')
                if len(fields) > 1:
                    name,filename = fields
                    seed = FCSeed(self.dir_seeds, name, filename)
                    self.add_seed(seed)
        except:
            log.error('Problem importing seed volumes from list file {}'.format(list_file))
            self.exit()
        finally:
            f.close()


    def extract_timecourse(self):
        log.info('Extracting timecourse signal for all seeds for all users...')
        reset_tasks()
        for stats in self.seed_stats:
            stats.extract_ts()
        wait_for_tasks()


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
            outfile = os.path.join(self.dir_grp_csv, 'fc_pearson_{}.csv'.format(seed.name))
            pearson_all.major_xs(seed.name).T.to_csv(outfile)

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


    def fc_voxelwise(self):
        reset_tasks()
        log.info('Producing voxelwise maps for all seeds for all sessions')
        for stats in self.seed_stats:
            stats.fc_voxelwise()
        wait_for_tasks()


    def fc_voxelwise_fisherz(self):
        reset_tasks()
        log.info('Converting r-maps to z-maps for all seeds for all sessions')
        for stats in self.seed_stats:
            stats.fc_voxelwise_fisherz()
        wait_for_tasks()

    def fc_voxelwise_all_groupstats(self, ttest=True):
        pool = reset_tasks()
        log.info('Running group-level stats for all seeds')
        for seed in self.seeds:
            pool.apply_async(self.fc_voxelwise_groupstats, (seed,ttest,))
        wait_for_tasks()

    def fc_voxelwise_groupstats(self, seed, ttest=True):
        zmaps = [s.file_zmap for s in self.seed_stats if s.seed == seed]
        zmaps_str = ' '.join(zmaps)

        # concatenate vols to temp file
        tmp = tempfile.mktemp(suffix='.nii.gz')
        cmd = "fslmerge -t {} {}".format(tmp, zmaps_str)
        run_cmd(cmd)

        # calculate mean z-map
        log.info('creating group mean z-map, roi={}'.format(seed.name))
        outfile = os.path.join(self.dir_grp_vols_mean, '{}_z_mean.nii.gz'.format(seed.name))
        cmd = "fslmaths {} -Tmean {}".format(tmp, outfile)
        run_cmd(cmd)

        ### graphics ###
        log.info('Generating snapshot image for results, roi={}'.format(seed.name))
        snap_img = os.path.join(self.dir_grp_imgs,
                                '{}_pearson_z_snapshot.png'.format(seed.name))
        snapshot_overlay(mri_standard, outfile, snap_img, vmin=.2, vmax=.7)

        # add to report
        self.report_seeds.add_img(seed.name, snap_img,
                                  'Group mean functional connectivity with {} (z(r) > 0.2)'.format(seed.name))

        # run t-test
        if ttest:
            log.info('running group t-test on z-maps, roi={}'.format(seed.name))
            outbase = os.path.join(self.dir_grp_vols_ttest, '{}.nii.gz'.format(seed.name))
            cmd = "3dttest++ -setA {} -prefix {} -mask {}".format(tmp, outbase, mri_brain_mask)
            run_cmd(cmd)

        # remove 4d file
        os.remove(tmp)

    def generate_report(self):

        # write to file
        log.info('Generating report...')
        report_file = os.path.join(self.dir_group, 'report.html')
        self.report.render_to_file(report_file)

        log.info('*********************************************')
        log.info('* report: {}'.format(report_file))
        log.info('*********************************************')


    def exit(self):
        # TODO: clean up anything?
        sys.exit()

