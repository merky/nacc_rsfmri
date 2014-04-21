#!/usr/bin/python

import os
import logging

########################
# settings
########################

# standard volume
mri_standard   = '{}/data/standard/MNI152_T1_2mm_brain.nii.gz'.format(os.environ['FSLDIR'])
mri_brain_mask = '{}/data/standard/MNI152_T1_2mm_brain_mask.nii.gz'.format(os.environ['FSLDIR'])

# fwhm
fwhm = 6

# directory where rsfmri_preproc output is located
restproc_dir = 'restproc'

# filename of preprocessed residual volume
#restproc_file = 'rest_reorient_skip_tc_mc_brain_atl_affine_fwhm%d_bpss_resid.nii.gz' % fwhm
restproc_file = 'rest_fwhm%d.nii.gz' % fwhm

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
