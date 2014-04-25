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
    maingroup.add_argument('--input', '-i', metavar='path', type=file_input_type, dest='sessdir',
                           help='Input directory containing pre-processed session directories',
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
    seedinput.add_argument('--coord', metavar=('name','x','y','z'), nargs=4, action='append',
                           help='Specify seed coordinates (x,y,z). Can use multiple times.')
    seedinput.add_argument('--coordlist', metavar='file', type=file_input_type,
                           help='File containing seed coordinates on each line (format: name, x, y, z, [radius])')
    seedinput.add_argument('--seedlist', metavar='file', type=file_input_type, dest='seedvollist',
                           help='File containing list of seed files on each line (format: name, file_location)')
    seedinput.add_argument('--seed', metavar=('name','file'), action='append', nargs=2, dest='seedvol',
                           help='Volume file to use as single seed. Can use multiple times.')

    # actions
    actgroup.add_argument('--skip-voxelwise', action='store_false', dest='voxelwise',
                          help="Skip voxelwise correlations; default is to run")
    actgroup.add_argument('--skip-matrix', action='store_false', dest='matrix',
                          help='Skip ROI-ROI correlations; default is to run')
    actgroup.add_argument('--ttest', action='store_true', default=False, dest='ttest',
                          help="Run group-level ttests; default is to skip")
    actgroup.add_argument('--skip-group-stats', action='store_false', dest='group_stats',
                          help='Skip all group-level stats; default is to run')
    actgroup.add_argument('--overwrite', '-W', action='store_true',
                          help='Force overwrite of existing output files')

    # options
    parser.add_argument('--radius', '-r', metavar='x', type=int,
                        help='Spherical radius (in mm) of seeds (required with --seed and overwrites any radius specified when using --coordlist)')
    parser.add_argument('--fwhm', '--smoothing', metavar='0/4/6', type=int, default=6, choices=[0,4,6],
                        help='Kernel size (in mm) for fwhm smoothing of preprocessed images (default 6mm; possible options: 0,4,6)')

    # parse user input
    args = parser.parse_args()

    # check that volume is file
    if args.seedvol is not None:
        for name, vol in args.seedvol:
            file_input_type(vol)


    # let's take a look at the seed argument, if available
    if getattr(args,'coord') is not None:
        # dependent on radius argument
        if getattr(args,'radius') is None:
            log.error('If coordinate input, must specify radius')
            sys.exit()

        # check that seed inputs are of correct type
        for seed in args.coord:
            try:
                name,x,y,z = seed
                seed = [name,float(x),float(y),float(z)]
            except:
                log.error('seed input not in correct format: {}'.format(seed))
                sys.exit()

    return args
