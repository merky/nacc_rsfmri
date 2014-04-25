#!/usr/bin/python

import os
import logging

########################
# settings
########################

# processes
max_num_threads = 40

# standard volume
mri_standard   = '{}/data/standard/MNI152_T1_2mm_brain.nii.gz'.format(os.environ['FSLDIR'])
mri_brain_mask = '{}/data/standard/MNI152_T1_2mm_brain_mask.nii.gz'.format(os.environ['FSLDIR'])

# fwhm
fwhm = 6

# directory where rsfmri_preproc output is located
restproc_dir = 'restproc'

# filename of preprocessed residual volume
# (found in subject's restproc dir)
restproc_file_template = 'rest_fwhm{}.nii.gz'

# log properties
log_filebase = 'analysis.log'
log_label    = 'rsfmri_analysis'
log_level    = logging.INFO

########################
# log
########################

log = logging.getLogger(log_label)
log.setLevel(logging.DEBUG)

# console output (INFO)
log_stream = logging.StreamHandler()
log_stream.setLevel(log_level)
log_format = logging.Formatter('%(levelname)s - %(message)s')
log_stream.setFormatter(log_format)
log.addHandler(log_stream)
