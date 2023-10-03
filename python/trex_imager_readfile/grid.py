import gzip
import numpy as np
import signal
import os
import h5py
from multiprocessing import Pool
from functools import partial

# static globals
__GRID_DT = np.dtype("uint8")
__EXPECTED_FRAME_COUNT = 20


def __grid_readfile_worker(file_obj):
    # init
    images = np.array([])
    metadata_dict_list = []
    problematic = False
    error_message = ""
    image_width = 0
    image_height = 0
    image_channels = 0
    image_dtype = __GRID_DT
    nframes = 0

    # open H5 file
    f = h5py.File(file_obj["filename"], 'r')

    # read data
    dset_images = f["data"]["images"]
    images = dset_images[()]
    images = np.moveaxis(images, [0, 1, 2, 3], [3, 0, 1, 2])

    # init metadata
    metadata = {}

    # read timestamps
    dset_timestamp = f["data"]["timestamp"]
    metadata["timestamp"] = dset_timestamp[()]

    # get file metadata
    metadata["file"] = {}
    mset_metadata_file = f["metadata"]["file"]
    for key in mset_metadata_file.attrs.keys():
        value = mset_metadata_file.attrs[key]
        metadata["file"][key] = value
    
    # get frame metadata
    metadata["frame"] = []
    for i in range(0, len(metadata["timestamp"])):
        




    # close H5 file
    f.close()

    # set image vars and reshape if multiple images
    image_height = images.shape[0]
    image_width = images.shape[1]
    image_channels = images.shape[2]
    if (len(images.shape) == 3):
        # single frame
        nframes = 1
        images = images.reshape((image_height, image_width, image_channels, 1))
    else:
        # multiple frames
        nframes = images.shape[3]

    # verify that metadata list size matches number of images
    if (len(metadata_dict_list) != nframes):
        problematic = True
        error_message = "Found different number of images and metadata records" \
            "(images=%d, metadata=%d)" % (nframes, len(metadata_dict_list))
        return images, metadata_dict_list, problematic, file_obj["filename"], error_message, \
            image_width, image_height, image_channels, image_dtype

    # return
    return images, metadata_dict_list, problematic, file_obj["filename"], error_message, \
        image_width, image_height, image_channels, image_dtype


def read(file_list, workers=1, quiet=False):
    """
    Read in a single PGM file or set of PGM files

    :param file_list: filename or list of filenames
    :type file_list: str
    :param workers: number of worker processes to spawn, defaults to 1
    :type workers: int, optional
    :param quiet: reduce output while reading data
    :type quiet: bool, optional

    :return: images, metadata dictionaries, and problematic files
    :rtype: numpy.ndarray, list[dict], list[dict]
    """
    # pre-allocate array sizes (optimization)
    predicted_num_frames = len(file_list) * __EXPECTED_FRAME_COUNT
    images = np.empty([512, 1024, predicted_num_frames], dtype=__GRID_DT)
    metadata_dict_list = [{}] * predicted_num_frames
    problematic_file_list = []

    # if input is just a single file name in a string, convert to a list to be fed to the workers
    if isinstance(file_list, str):
        file_list = [file_list]

    # check workers
    if (workers > 1):
        try:
            # set up process pool (ignore SIGINT before spawning pool so child processes inherit SIGINT handler)
            original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
            pool = Pool(processes=workers)
            signal.signal(signal.SIGINT, original_sigint_handler)  # restore SIGINT handler
        except ValueError:
            # likely the read call is being used within a context that doesn't support the usage
            # of signals in this way, proceed without it
            pool = Pool(processes=workers)

        # call readfile function, run each iteration with a single input file from file_list
        # NOTE: structure of data - data[file][metadata dictionary lists = 1, images = 0][frame]
        data = []
        try:
            data = pool.map(partial(__grid_readfile_worker, quiet=quiet), file_list)
        except KeyboardInterrupt:
            pool.terminate()  # gracefully kill children
            return np.empty((0, 0, 0), dtype=__GRID_DT), [], []
        else:
            pool.close()
            pool.join()
    else:
        # don't bother using multiprocessing with one worker, just call the worker function directly
        data = []
        for f in file_list:
            data.append(__grid_readfile_worker(f, quiet=quiet))

    # reorganize data
    list_position = 0
    for i in range(0, len(data)):
        # check if file was problematic
        if (data[i][2] is True):
            problematic_file_list.append({
                "filename": data[i][3],
                "error_message": data[i][4],
            })

        # check if any data was read in
        if (len(data[i][1]) == 0):
            continue

        # find actual number of frames, this may differ from predicted due to dropped frames, end
        # or start of imaging
        real_num_frames = data[i][0].shape[2]

        # metadata dictionary list at data[][1]
        metadata_dict_list[list_position:list_position + real_num_frames] = data[i][1]
        images[:, :, list_position:list_position + real_num_frames] = data[i][0]  # image arrays at data[][0]
        list_position = list_position + real_num_frames  # advance list position

    # trim unused elements from predicted array sizes
    metadata_dict_list = metadata_dict_list[0:list_position]
    images = np.delete(images, range(list_position, predicted_num_frames), axis=2)

    # ensure entire array views as uint16
    images = images.astype(np.uint16)

    # return
    data = None
    return images, metadata_dict_list, problematic_file_list
