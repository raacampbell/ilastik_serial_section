# ilastik_serial_section

The repo houses a loose collection of functions for assisting processing of mouse brain serial section data with Ilastik.



## Installation
No installer yet, just add to Python path. One nice way of doing this if you use IPython:

If needed first make a config file.

```
$ ipython profile create
```

Now you can edit the list `c.InteractiveShellApp.exec_lines` in  `~/.ipython/profile_default/ipython_config.py`

For example:
```
c.InteractiveShellApp.exec_lines = ['import sys,os',
                                    'from importlib import reload',
                                    'import numpy as np',
                                    'import matplotlib.pyplot as plt',
                                    'plt.ion();',
                                    'sys.path.append("/home/user/Code/python/ilastik_serial_section");']
```



## Example
```
import ilastikss.munge
import ilastikss.io
```


Some pipelines run faster with 8 bit images or just do not require 16 bit resolution. In these cases
you can convert everything to 8 bit, which will cut disk usage in half. You will need to make a temporary
directory, place converted files there. Then replace the originals:

```
mkdir tmp
ilastikss.munge.convert8bit('stitchedImages_100/2','tmp')
rm -frv stitchedImages_100/2/*.tif
mv tmp/*.tif  stitchedImages_100/2/
ls -l stitchedImages_100/2/*.tif | wc -l # confirming they all moved
```


Say now you have run an Ilastik classifier on a dataset and produced one labels hdf5 ('.h5') file
per image. We want to convert these to compressed TIFFs as this will save a vast quantity of disk
space:


```
# cd to some path containing the label files
cd /mnt/btrfs/TM_RML_FVB/8bit_chan2/attempt03
files=ilastikss.io.get_files_with_extension_from_dir(ext='.h5')
[ilastikss.munge.resave_ilastik_data_as_compressed_tiff(t_file) for t_file in files]
```


We can now generate a 3D downsampled stack of these. We select label 2 in this case as the label
we want to retain.
```
# Directory where label files exist
S = "/mnt/btrfs/TM_RML_FVB_120dpi/8bit_chan2/size_050/attempt03"

# Downsampled stacks dir into which we will add the labels image stack
D = "DS_VERSION/downsampled_stacks/025_micron/"

# Generate the downsampled 3D stack using label 2, which in this case the label of interest because
# label 1 is used to denote false positives. This function will save a compressed multi-page TIFF
# into D and also use existing stacks in this directory to determine the correct image size for the
# labels stack.

ilastikss.munge.generate_3D_label_volume(S,D,label=2)
```


