# Author: Lukas Vollmerhaus
# Date: 2020-10-16

import gzip as _gzip
import numpy as _np
import signal as _signal
import cv2 as _cv2
import tarfile as _tarfile
import os as _os
import datetime as _datetime
from multiprocessing import Pool as _Pool

# static globals
__RGB_PGM_IMAGE_SIZE_BYTES = 480 * 553 * 2
__RGB_PGM_DT = _np.dtype("uint16")
__RGB_PGM_DT = __RGB_PGM_DT.newbyteorder('>')  # force big endian byte ordering
__RGB_PNG_DT = _np.dtype("uint8")
__PNG_METADATA_PROJECT_UID = "trex"

# dynamic globals
__worker_tar_tempdir = ""


def read(file_list, workers=1, tar_tempdir="."):
    """
    Read in a single PGM or PNG.TAR file, or an array of them. All files
    must be the same type.

    :param file_list: filename or list of filenames
    :type file_list: str
    :param workers: number of worker processes to spawn, defaults to 1
    :type workers: int, optional
    :param tar_tempdir: path to untar to, defaults to '.'
    :type tar_tempdir: str, optional

    :return: images, metadata dictionaries, and problematic files
    :rtype: numpy.ndarray, list[dict], list[dict]
    """
    # set globals
    global __worker_tar_tempdir
    __worker_tar_tempdir = tar_tempdir

    # set up process pool (ignore SIGINT before spawning pool so child processes inherit SIGINT handler)
    original_sigint_handler = _signal.signal(_signal.SIGINT, _signal.SIG_IGN)
    pool = _Pool(processes=workers)
    _signal.signal(_signal.SIGINT, original_sigint_handler)  # restore SIGINT handler

    # if input is just a single file name in a string, convert to a list to be fed to the workers
    if isinstance(file_list, str):
        file_list = [file_list]

    # call readfile function, run each iteration with a single input file from file_list
    pool_data = []
    try:
        pool_data = pool.map(__trex_readfile_worker, file_list)
    except KeyboardInterrupt:
        pool.terminate()  # gracefully kill children
    else:
        pool.close()

    # set sizes
    image_width = pool_data[0][5]
    image_height = pool_data[0][6]
    image_channels = pool_data[0][7]
    image_dtype = pool_data[0][8]
    expected_frame_count = pool_data[0][0].shape[-1]

    # pre-allocate array sizes (optimization)
    predicted_num_frames = len(file_list) * expected_frame_count
    if (image_channels > 1):
        images = _np.empty([image_width, image_height, image_channels, predicted_num_frames], dtype=image_dtype)
    else:
        images = _np.empty([image_width, image_height, predicted_num_frames], dtype=image_dtype)
    metadata_dict_list = [{}] * predicted_num_frames
    problematic_file_list = []

    # reorganize data
    list_position = 0
    for i in range(0, len(pool_data)):
        # check if file was problematic
        if (pool_data[i][2] is True):
            problematic_file_list.append({
                "filename": pool_data[i][3],
                "error_message": pool_data[i][4],
            })

        # check if any data was read in
        if (len(pool_data[i][1]) == 0):
            continue

        # find actual number of frames, this may differ from predicted due to dropped frames, end
        # or start of imaging
        real_num_frames = pool_data[i][0].shape[-1]

        # metadata dictionary list at data[][1]
        metadata_dict_list[list_position:list_position + real_num_frames] = pool_data[i][1]
        if (image_channels > 1):
            images[:, :, :, list_position:list_position + real_num_frames] = pool_data[i][0]
        else:
            images[:, :, list_position:list_position + real_num_frames] = pool_data[i][0]
        list_position = list_position + real_num_frames  # advance list position

    # trim unused elements from predicted array sizes
    metadata_dict_list = metadata_dict_list[0:list_position]
    if (image_channels > 1):
        images = _np.delete(images, range(list_position, predicted_num_frames), axis=3)
    else:
        images = _np.delete(images, range(list_position, predicted_num_frames), axis=2)

    # ensure entire array views as the dtype
    images = images.astype(image_dtype)

    # return
    pool_data = None
    return images, metadata_dict_list, problematic_file_list


def __trex_readfile_worker(file):
    # init
    images = _np.array([])
    metadata_dict_list = []
    problematic = False
    error_message = ""
    image_width = 0
    image_height = 0
    image_channels = 0
    image_dtype = _np.dtype("uint16")
    image_dtype = image_dtype.newbyteorder('>')

    # check file extension to know how to process
    try:
        if (file.endswith("pgm") or file.endswith("pgm.gz")):
            return __rgb_readfile_worker_pgm(file)
        elif (file.endswith("png") or file.endswith("png.tar")):
            return __rgb_readfile_worker_png(file)
        else:
            print("Unrecognized file type: %s" % (file))
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Failed to process file '%s' " % (file))
        problematic = True
        error_message = "failed to process file: %s" % (str(e))
    return images, metadata_dict_list, problematic, file, error_message, \
        image_width, image_height, image_channels, image_dtype


def __rgb_readfile_worker_pgm(file):
    # init
    images = _np.array([])
    metadata_dict_list = []
    first_frame = True
    metadata_dict = {}
    site_uid = ""
    device_uid = ""
    problematic = False
    error_message = ""
    image_width = 480
    image_height = 553
    image_channels = 1
    image_dtype = __RGB_PGM_DT

    # check file extension to see if it's gzipped or not
    try:
        if file.endswith("pgm.gz"):
            unzipped = _gzip.open(file, mode='rb')
        elif file.endswith("pgm"):
            unzipped = open(file, mode='rb')
        else:
            print("Unrecognized file type: %s" % (file))
            return images, metadata_dict_list, problematic, file, error_message, \
                image_width, image_height, image_channels, image_dtype
    except Exception as e:
        print("Failed to open file '%s' " % (file))
        problematic = True
        error_message = "failed to open file: %s" % (str(e))
        return images, metadata_dict_list, problematic, file, error_message, \
            image_width, image_height, image_channels, image_dtype

    # read the file
    while True:
        # read a line
        try:
            line = unzipped.readline()
        except Exception as e:
            print("Error reading before image data in file '%s'" % (file))
            problematic = True
            metadata_dict_list = []
            images = _np.array([])
            error_message = "error reading before image data: %s" % (str(e))
            return images, metadata_dict_list, problematic, file, error_message, \
                image_width, image_height, image_channels, image_dtype

        # break loop at end of file
        if (line == b''):
            break

        # magic number; this is not a metadata or image line, exclude
        if (line.startswith(b'P5\n')):
            continue

        # process line
        if (line.startswith(b'#"')):
            # metadata lines start with #"<key>"
            try:
                line_decoded = line.decode("ascii")
            except Exception as e:
                # skip metadata line if it can't be decoded, likely corrupt file
                print("Error decoding metadata line: %s (line='%s', file='%s')" % (str(e), line, file))
                problematic = True
                error_message = "error decoding metadata line: %s" % (str(e))
                continue

            # split the key and value out of the metadata line
            line_decoded_split = line_decoded.split('"')
            key = line_decoded_split[1]
            value = line_decoded_split[2].strip()

            # add entry to dictionary
            if (key in metadata_dict):
                # key already exists, turn existing value into list and append new value
                if (isinstance(metadata_dict[key], list)):
                    # is a list already
                    metadata_dict[key].append(value)
                else:
                    metadata_dict[key] = [metadata_dict[key]]
            else:
                # normal metadata value
                metadata_dict[key] = value

            # set the site/device uids, or inject the site and device UIDs if they are missing
            if ("Site unique ID" not in metadata_dict):
                metadata_dict["Site unique ID"] = site_uid
            else:
                site_uid = metadata_dict["Site unique ID"]
            if ("Imager unique ID" not in metadata_dict):
                metadata_dict["Imager unique ID"] = device_uid
            else:
                device_uid = metadata_dict["Imager unique ID"]

            # split dictionaries up per frame, exposure plus initial readout is
            # always the end of metadata for frame
            if (key.startswith("Effective image exposure")):
                metadata_dict_list.append(metadata_dict)
                metadata_dict = {}
        elif line == b'65535\n':
            # there are 2 lines between "exposure plus read out" and the image
            # data, the first is b'480 553\n' and the second is b'65535\n'
            #
            # read image
            try:
                # read the image size in bytes from the file
                image_bytes = unzipped.read(__RGB_PGM_IMAGE_SIZE_BYTES)

                # format bytes into numpy array of unsigned shorts (2byte numbers, 0-65536),
                # effectively an array of pixel values
                image_np = _np.frombuffer(image_bytes, dtype=__RGB_PGM_DT)

                # change 1d numpy array into 480x553 matrix with correctly located pixels
                image_matrix = _np.reshape(image_np, (480, 553, 1))
            except Exception as e:
                print("Failed reading image data frame: %s" % (str(e)))
                metadata_dict_list.pop()  # remove corresponding metadata entry
                problematic = True
                error_message = "image data read failure: %s" % (str(e))
                continue  # skip to next frame

            # initialize image stack
            if first_frame:
                images = image_matrix
                first_frame = False
            else:
                images = _np.dstack([images, image_matrix])  # depth stack images (on 3rd axis)

    # close gzip file
    unzipped.close()

    # return
    return images, metadata_dict_list, problematic, file, error_message, \
        image_width, image_height, image_channels, image_dtype


def __rgb_readfile_worker_png(file):
    # init
    images = _np.array([])
    metadata_dict_list = []
    problematic = False
    first_frame = True
    error_message = ""
    image_width = 0
    image_height = 0
    image_channels = 0
    image_dtype = __RGB_PNG_DT
    is_tar_file = False

    # check if it's a tar file
    file_list = []
    if (file.endswith(".png.tar")):
        # tar file, extract all frames and add to list
        try:
            tf = _tarfile.open(file)
            file_list = sorted(tf.getnames())
            tf.extractall(path=__worker_tar_tempdir)
            for i in range(0, len(file_list)):
                file_list[i] = "%s/%s" % (__worker_tar_tempdir, file_list[i])
            tf.close()
            is_tar_file = True
        except Exception as e:
            if ("file_list" in locals()):
                # cleanup
                for f in file_list:
                    try:
                        _os.remove(f)
                    except Exception:
                        pass
            print("Failed to open file '%s' " % (file))
            problematic = True
            error_message = "failed to open file: %s" % (str(e))
            return images, metadata_dict_list, problematic, file, error_message, \
                image_width, image_height, image_channels, image_dtype
    else:
        # regular png
        file_list = [file]

    # read each png file
    for f in file_list:
        # process metadata
        try:
            # set metadata values
            file_split = _os.path.basename(f).split('_')
            site_uid = file_split[3]
            device_uid = file_split[4]
            exposure = "%.03f ms" % (float(file_split[5][:-2]))
            mode_uid = file_split[6][:-4]
            timestamp = _datetime.datetime.strptime("%sT%s" % (file_split[0], file_split[1]), "%Y%m%dT%H%M%S")

            # set the metadata dict
            metadata_dict = {
                "Project unique ID": __PNG_METADATA_PROJECT_UID,
                "Site unique ID": site_uid,
                "Imager unique ID": device_uid,
                "Mode unique ID": mode_uid,
                "Image request start": timestamp,
                "Subframe requested exposure": exposure,
            }
            metadata_dict_list.append(metadata_dict)
        except Exception as e:
            print("Failed to read metadata from file '%s' " % (f))
            problematic = True
            error_message = "failed to read metadata: %s" % (str(e))
            break

        # read png file
        try:
            # read file
            image_np = _cv2.imread(f)
            image_width = image_np.shape[0]
            image_height = image_np.shape[1]
            image_channels = image_np.shape[2] if len(image_np.shape) > 2 else 1
            if (image_channels > 1):
                image_matrix = _np.reshape(image_np, (image_width, image_height, image_channels, 1))
            else:
                image_matrix = _np.reshape(image_np, (image_width, image_height, 1))

            # initialize image stack
            if (first_frame is True):
                images = image_matrix
                first_frame = False
            else:
                if (image_channels > 1):
                    images = _np.concatenate([images, image_matrix], axis=3)  # concatenate (on last axis)
                else:
                    images = _np.dstack([images, image_matrix])  # depth stack images (on last axis)
        except Exception as e:
            print("Failed reading image data frame: %s" % (str(e)))
            metadata_dict_list.pop()  # remove corresponding metadata entry
            problematic = True
            error_message = "image data read failure: %s" % (str(e))
            continue  # skip to next frame

    # remove untarred files
    if (is_tar_file is True):
        for f in file_list:
            _os.remove(f)

    # return
    return images, metadata_dict_list, problematic, file, error_message, \
        image_width, image_height, image_channels, image_dtype
