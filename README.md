### Current Requirements
showing version(s) currently tested...

* FSL (version 5.0+)
* AFNI (version AFNI_2011_12_21_1014)
* SPM8 (normalization)
* Advanced Normalization Tools (version 1.9.2)


### Preprocessing
Note: It is very important that the correct TR is specified in 
the header of the input file(s). Please double-check before
pre-processing!

```bash
rsfmri_preproc <outputdir>/<subjid> \
               <path-to>/anat.nii.gz \
               <path-to>/func1.nii.gz [<path-to>/func2.nii.gz]
```


### Analysis

```bash
rsfmri_conn --help
```

will display command-line options
