#!/usr/bin/python

import os
import re
import sys
from shutil import copyfile

# our files
from settings import *
from graphics import snapshot_overlay
from utils    import run_cmd, check_file

# helper function

def create_seeds_from_file(output_dir, list_file, radius=None):
    # creates spherical ROIs from x,y,z coordinates in file
    #  * each line should be: name, x, y, z, radius
    #  * radius is optional
    log.info('Creating seeds from MNI coords specified in list file: {}'.format(list_file))

    # open the file up and loop through each row
    f = open(check_file(list_file), 'r')
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
            x,y,z = [float(j.strip()) for j in fields[1:4]]
            # radius is optional, so we need to check that it was specified somewhere
            if radius is None:
                if len(fields) == 5:
                    seed_radius = float(fields[4].strip())
                else:
                    log.error('When creating seed from a file, you must specify the radius in the file itself or on the command line')
                    sys.exit()
            else:
                seed_radius = radius

            # create seed
            seed = FCSeed(output_dir, n)
            seed.create(x,y,z,seed_radius)
            yield seed
    except:
        log.error('Problem importing seed coordinates from file {}'.format(list_file))
        sys.exit()
    finally:
        f.close()



# the seed class

class FCSeed(object):
    def __init__(self, seed_dir, name, file=None):
        self.name          = name
        self.dir           = seed_dir
        self.file_snapshot = os.path.join(self.dir, 'seed_{}.png'.format(self.name))
        self.file          = file

        if self.file is not None: self.set(os.path.abspath(file))

    def create(self, x, y, z, radius):
        log.info('Creating spherical seed NAME={} MNI=({},{},{}) RADIUS={}mm'.format(self.name,x,y,z,radius))

        self.file = os.path.join(self.dir, '%s_%dmm.nii.gz' % (self.name, radius,))
        cmd = '3dUndump -prefix {ofile} -xyz -orient LPI -master {std} -srad {rad} <(echo \'{x} {y} {z}\')' \
                .format(ofile = self.file,
                        std   = mri_standard,
                        rad   = radius,
                        x     = x,
                        y     = y,
                        z     = z)

        run_cmd(cmd) # blocking

    def take_snapshot(self):
        log.info('Taking snapshot image of seed \'{}\''.format(self.name))

        snapshot_overlay(mri_standard, self.file, self.file_snapshot, auto_coords=True)

    def set(self, file):
        seed_file = os.path.join(self.dir, os.path.basename(file))
        if seed_file != file:
            # copy seed file over to project directory, if needed
            log.info('copying seed file into project: {}'.format(file))
            copyfile(file, seed_file)

        # update
        self.file = seed_file
