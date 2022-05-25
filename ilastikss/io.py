""" Very simple general-purpose functions for loading, saving, returning file lists, etc
"""

import os

def get_files_with_extension_from_dir(in_dir='./', ext=''):
    """ Return a list of files with a given extension from a directory

    Inputs
    ------
    in_dir : str
       The relative or absolute path of a directory that contains files to be listed. By default
       this is the current directory
    ext : str
       The extension to search for. (Uses endswith to do this, so you do not have to restrict
       yourself to searching for the extension only.


    Returns
    -------
    list
    A list of files at this path.
    """


    if len(ext)==0:
        return []

    if not os.path.isdir(in_dir):
        print('in_dir is not a dirctory')
        return None


    file_list = []
    for t_file in os.listdir(os.path.join(in_dir)):
        if t_file.endswith(ext):
            file_list.append(t_file)

    # Ensure file list is in order
    file_list.sort()

    return file_list

