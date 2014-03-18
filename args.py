#!/usr/bin/python

import os
import sys
import argparse

# our files
from settings import *

########################
# arguments
########################

# helper (file)
def file_input_type(x):
    if not os.path.exists(x):
        log.error('File cannot be found: {}'.format(x))
    return x

def parse_args():
    parser    = argparse.ArgumentParser(description='Run rs-fmri functional connectivity')
    maingroup = parser.add_argument_group(title='required')
    sessgroup = parser.add_argument_group(title='sessions (pick one)')
    seedgroup = parser.add_argument_group(title='seeds (pick one)')
    actgroup  = parser.add_argument_group(title='actions')

    sessinput = sessgroup.add_mutually_exclusive_group(required=True)
    seedinput = seedgroup.add_mutually_exclusive_group(required=True)

    # main
    maingroup.add_argument('--sessdir', '-d', metavar='path', type=file_input_type,
                           help='Input directory containing session directories',
                           required=True)
    maingroup.add_argument('--output', '-o', metavar='path', type=file_input_type,
                           help='Output directory (will create child directory with analysis label name)',
                           required=True)
    maingroup.add_argument('--label', '-l', metavar='name',
                           help='Name of current analysis (creates directory)',
                           required=True)
    # session(s)
    sessinput.add_argument('--session', '-s', metavar='id', action='append',
                           help='Session ID (located in input directory). Can use multiple times.')
    sessinput.add_argument('--sesslist', metavar='file', type=file_input_type,
                           help='File containing list of session IDs (located in input directory)')

    # seed(s)
    seedinput.add_argument('--seed', '--coord', metavar=('name','x','y','z'), nargs=4, action='append',
                           help='Specify seed coordinates (x,y,z). Can use multiple times.')
    seedinput.add_argument('--coordlist', metavar='file', type=file_input_type,
                           help='File containing seed coordinates on each line (format: name, x, y, z, [radius])')
    seedinput.add_argument('--seedlist', metavar='file', type=file_input_type,
                           help='File containing list of seed files on each line (format: name, file_location)')
    seedinput.add_argument('--seedvol', metavar=('name','file'), action='append', nargs=2,
                           help='Volume file to use as single seed. Can use multiple times.')

    # actions
    actgroup.add_argument('--skip-voxelwise', action='store_false', dest='voxelwise',
                          help="Skip voxelwise correlations; default is to run")
    actgroup.add_argument('--skip-matrix', action='store_false', dest='matrix',
                          help='Skip ROI-ROI correlations, default is to run')
    actgroup.add_argument('--skip-group-stats', action='store_false', dest='group_stats',
                          help='Skip group-level stats, default is to run')
    actgroup.add_argument('--overwrite', '-W', action='store_true',
                        help='Force overwrite of existing output files')

    # options
    parser.add_argument('--radius', '-r', metavar='x', type=int,
                           help='Spherical radius (in mm) of seeds (required with --seed and overwrites any radius specified when using --coordlist)')

    # parse user input
    args = parser.parse_args()

    # check that volume is file
    if args.seedvol is not None:
        for name, vol in args.seedvol:
            file_input_type(vol)


    # let's take a look at the seed argument, if available
    if getattr(args,'seed') is not None:
        # dependent on radius argument
        if getattr(args,'radius') is None:
            log.error('If coordinate input, must specify radius')
            sys.exit()

        # check that seed inputs are of correct type
        for seed in args.seed:
            try:
                name,x,y,z = seed
                seed = [name,float(x),float(y),float(z)]
            except:
                log.error('seed input not in correct format: {}'.format(seed))
                sys.exit()

    return args
