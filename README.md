### Current Requirements
showing version(s) currently tested...

* FSL (version 5.0+)
* AFNI (version AFNI_2011_12_21_1014)
* Advanced Normalization Tools (version 1.9.2)


### Preprocessing

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
