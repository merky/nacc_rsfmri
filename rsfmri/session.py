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
    def __init__(self, session_id, parent_dir, fwhm):
        self.parent_dir  = parent_dir
        self.id    = session_id
        self.dir   = os.path.join(self.parent_dir, self.id)
        self.stats = []

        # bold file
        restproc_file = restproc_file_template.format(fwhm)
        self.bold  = os.path.join(self.dir, restproc_dir, restproc_file)

        if not os.path.isdir(self.dir):
            log.error('cannot find dir: {}'.format(self.dir))
            sys.exit()

        if not os.path.isfile(self.bold):
            log.error('cannot find file: {}'.format(self.bold))
            sys.exit()


    def add_stats(self, stats):
        self.stats.append(stats)

    def timecourse(self):
        d = {s.seed.name:np.genfromtxt(s.file_ts) for s in self.stats}
        return pd.DataFrame(d)

    def fcmatrix(self):
        return self.timecourse().corr()
