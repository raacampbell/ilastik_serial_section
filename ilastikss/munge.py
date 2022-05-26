
import cv2
import numpy as np
import skimage, skimage.io, skimage.transform
import ilastikss.io as issio
from os import listdir
from os.path import join, isdir, isfile
from skimage.measure import block_reduce


def convert8bit(in_dir, out_dir, my_alpha=0.003, overwrite=False):
    '''
    Convert all TIFFs in a directory from 16 bit to 8 bit using opencv

    Inputs
    ------
    in_dir : Relative or absolute path to the directory that contains images to convert.
    out_dir : Relative or absolute path to the directory into which converted data will be stored.
    my_alpha : Alpha value for the 8 bit conversion. Equals 0.003 by default.
    overwrite : If true, we overwrite data that have already been writen. False by default.
    '''
    if not isdir(in_dir):
        print('No such directory %s. Quitting.' % in_dir)
        return

    if not isdir(out_dir):
        print('No such directory %s. Quitting.' % out_dir)
        return


    file_list = issio.get_files_with_extension_from_dir(in_dir, '.tif')

    if len(file_list) == 0:
        print('No TIF files in directory %s. Quitting.' % in_dir)
        return

    print('Found %d TIFs in directory %s' % (len(file_list), in_dir))


    for t_file in file_list:
        save_fname = join(out_dir, t_file) # Save to this location

        if isfile(join(out_dir,t_file)) and not overwrite:
            # Skip if we don't overwrite and file exists
            continue

        print('Processing %s' % t_file)
        im = skimage.io.imread(join(in_dir, t_file))
        im = cv2.convertScaleAbs(im, alpha=my_alpha) # Convert to 8 bit

        skimage.io.imsave(save_fname, im)


def rescaleImages(in_dir, out_dir, rescale_proportion, overwrite=False):
    '''
    Rescale all TIFFs in directory. rescale_proportion should be a number
    between 0 and 1.


    Inputs
    ------
    in_dir : Relative or absolute path to the directory that contains images to convert.
    out_dir : Relative or absolute path to the directory into which converted data will be stored.
    rescale_proportion : scalar between 0 and 1. e.g. 0.5 reduce size by 50%.
    overwrite : If true, we overwrite data that have already been writen. False by default.
    '''
    if not isdir(in_dir):
        print('No such directory %s. Quitting.' % in_dir)
        return

    if not isdir(out_dir):
        print('No such directory %s. Quitting.' % out_dir)
        return


    file_list = issio.get_files_with_extension_from_dir(in_dir,'.tif')

    if len(file_list) == 0:
        print('No TIF files in directory %s. Quitting.' % in_dir)
        return

    print('Found %d TIFs in directory %s' % (len(file_list), in_dir))


    for t_file in file_list:
        save_fname = join(out_dir, t_file) # Save to this location

        if isfile(save_fname) and not overwrite:
            # Skip if we don't overwrite and file exists
            continue

        print('Processing %s' % t_file)
        im = skimage.io.imread(join(in_dir, t_file))

        x_new = int(im.shape[1] * rescale_proportion)
        y_new = int(im.shape[0] * rescale_proportion)

        im = cv2.resize(im, (x_new, y_new), interpolation=cv2.INTER_NEAREST)

        skimage.io.imsave(save_fname, im)



def get_exported_ilastik_label_from_file(fname, rescale_xy=1.0, label=0):
    '''
    Load Ilastik label file saves as a TIFF. Extract labels of interest and optionally rescale.
    The rescale maintains knowledge of the number hits per pixel. So if we
    we have to rescale by 20 by 20, then it sums in blocks of 20 by 20.

    If label is 0 it returns all labels. Otherwise returns the selected label.

    rescale_xy can be a scalar, in which case image is rescaled by this amount
    or (cols,rows) vector indicating target size.
    '''

    exp_data = skimage.io.imread(fname)

    if label > 0:
        exp_data = exp_data == label

    do_rescale = False

    if not isinstance(rescale_xy, tuple) and not isinstance(rescale_xy, list) and rescale_xy < 1:
        # This is the final resize that we need
        x_new = int(exp_data.shape[1] * rescale_xy)
        y_new = int(exp_data.shape[0] * rescale_xy)

        # But first we block resize
        resize_by = int(np.round(1/rescale_xy))
        do_rescale = True

    elif isinstance(rescale_xy, tuple) and len(rescale_xy) == 2:
        resize_by = int(np.round(exp_data.shape[0]/rescale_xy[0]))
        x_new = rescale_xy[1]
        y_new = rescale_xy[0]
        do_rescale = True

    if do_rescale:
        exp_data = block_reduce(exp_data, (resize_by, resize_by), func=np.sum)

        # Now we finish off by getting to exactly the size we want
        exp_data = cv2.resize(exp_data, [x_new, y_new], interpolation=cv2.INTER_NEAREST)

    return exp_data


def generate_3D_label_volume(label_dir, downsample_dir, label=0):
    ''' Generate a downsampled 3-D volume of labels from a series of separate label TIFFs

    Purpose
    -------
    We assume the user has converted Ilastik .h5 label files into compressed TIFFs using
    the function resave_ilastik_data_as_compressed_tiff from this module. These files are to
    be saved in their own directory. This function gets as input this directory and also the path to
    a downsampled stack directory. It extracts the image size of the downsampled stacks and
    downsamples the label arrays to the same size. Then saves the labels in this directory.

    Inputs
    ------
    label_dir : Relative or absolute path to compressed TIFF label images
    downsample_dir : Relative or absolute path to downsampled stack directory
    label : The label ID we are to extract. If zero, all labels are extracted
    '''
    if not isdir(label_dir):
        print('No such directory %s. Quitting.' % label_dir)
        return

    if not isdir(downsample_dir):
        print('No such directory %s. Quitting.' % downsample_dir)
        return

    extension = '.tiff' # The extension of the files we are searching for in label_dir
    file_list = issio.get_files_with_extension_from_dir(label_dir, extension)

    if file_list is None or len(file_list) == 0:
        print('No files in directory %s. Quitting.' % label_dir)
        return

    print('Found %d files in directory %s' % (len(file_list), label_dir))


    # Get the target directory size
    target_size = target_im_size_from_dir(downsample_dir)


    # Load first and pre-allocate the array
    im = get_exported_ilastik_label_from_file(join(label_dir, file_list[0]), target_size[1:], label)

    OUT = np.zeros( (len(file_list), im.shape[0], im.shape[1]), dtype=np.int16 )

    t_slice = 0
    for t_file in file_list:
        fname = join(label_dir, t_file)
        if isfile(fname):
            print('Loading %s' % t_file)
            im = get_exported_ilastik_label_from_file(fname, target_size[1:], label)
            OUT[t_slice, :, :] = im
            t_slice += 1


    OUT = skimage.transform.resize(OUT.astype(float), target_size, anti_aliasing=False)

    label_fname = ('ilastik_label_%d.tif' % label)
    skimage.io.imsave(join(downsample_dir,label_fname), OUT.astype('int16'), compression="zlib")

    return OUT


def resave_ilastik_data_as_compressed_tiff(fname, overwrite=False):
    '''Resave Ilastik hdf5 file as a compressed TIFF

    Purpose
    -------
    Ilastik by default returns label files as hdf5 where the classification results are stored in
    an array. By default the array seems to be int8. This is really inefficient if only a small
    number of label classes exists and for large images the resulting data size is huge. If we
    re-save as compressed TIFF then there is a huge reduction in disk usage. Three orders of
    magnitude is roughly what you can expect.


    Inputs
    ------
    fname - str
       A string representing the relative or absolute path to the hdf5 file to convert

    overwrite -- bool
       False by default. If True we overwrite TIFFs that were already generated.

    Outputs   None
    -------
    New files automatically produced in the same path as the original files. The extension is
    changed and the space in the file name changed to an underscore.

    '''

    tiff_fname = fname.replace(" Predictions.h5", "_Predictions.tiff")

    if isfile(tiff_fname) and not overwrite:
        return

    print('Making %s' % tiff_fname)
    im_data = get_exported_ilastik_label_from_file(fname)
    skimage.io.imsave(tiff_fname, im_data, compression="zlib")



def target_im_size_from_dir(IN):
    '''Get the downsampled stack image dimensions from a downsampled directory name or image


    Inputs
    ------
    IN : Either a relative or absolute path to a stitchit downsampled stack dir or to a downsampled
        TIFF.

    Outputs
    -------
    im shape : a tuple being (num planes, pixel xy rows, pixel xy columns)

    '''


    if isdir(IN):
        t_im = issio.get_files_with_extension_from_dir(IN, 'tif')
        im_path = join(IN,t_im[0])
    else:
        im_path = IN

    if not isfile(im_path):
        print('%s is not a valid file path' % im_path)


    im = skimage.io.imread(im_path)

    return im.shape
