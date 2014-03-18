#!/usr/bin/python

import os
import sys
import numpy as np
import pandas as pd

# our imports
from settings import *

##########################
# session
##########################

class FCSession(object):
    files = {'zmap': {}, 'rmap': {}, 'ts': {}}

    def __init__(self, session_id, parent_dir):
        self.id   = session_id
        self.parent_dir  = parent_dir
        self.dir  = os.path.join(self.parent_dir, self.id)
        self.bold = os.path.join(self.dir, restproc_dir, restproc_file)

        if not os.path.isdir(self.dir):
            log.error('cannot find dir: {}'.format(self.dir))
            sys.exit()

        if not os.path.isfile(self.bold):
            log.error('cannot find file: {}'.format(self.bold))
            sys.exit()

    def check_file(self, file_loc):
        if not os.path.isfile(file_loc):
            log.error('cannot find file: {}'.format(file_loc))
            sys.exit()

        return file_loc

    def set_zmap_file(self, seed_name, file_loc):
        self.files['zmap'][seed_name] = self.check_file(file_loc)

    def set_rmap_file(self, seed_name, file_loc):
        self.files['rmap'][seed_name] = self.check_file(file_loc)

    def set_ts_file(self, seed_name, file_loc):
        self.files['ts'][seed_name] = self.check_file(file_loc)

    def get_zmap_file(self, seed_name):
        return self.files['zmap'][seed_name]

    def get_rmap_file(self, seed_name):
        return self.files['rmap'][seed_name]

    def get_ts_file(self, seed_name):
        return self.files['ts'][seed_name]

    def timecourse(self):
        d = {}
        for seed,tsfile in self.files['ts'].iteritems():
            d[seed] = np.genfromtxt(tsfile)
        return pd.DataFrame(d)

    def fcmatrix(self):
        return self.timecourse().corr()
