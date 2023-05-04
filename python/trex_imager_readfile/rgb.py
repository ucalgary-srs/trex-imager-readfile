import gzip
import numpy as np
import signal
import cv2
import tarfile
import os
import datetime
import h5py
from pathlib import Path
from multiprocessing import Pool

# static globals
__RGB_PGM_IMAGE_SIZE_BYTES = 480 * 553 * 2
__RGB_PGM_DT = np.dtype("uint16")
__RGB_PGM_DT = __RGB_PGM_DT.newbyteorder('>')  # force big endian byte ordering
__RGB_PNG_DT = np.dtype("uint8")
__RGB_H5_DT = np.dtype("uint8")
__PNG_METADATA_PROJECT_UID = "trex"
__FLEX_NOMINAL_FRAME_COUNT = 2
__FLEX_BURST_FRAME_COUNT = 50
__EXPECTED_NOMINAL_FRAME_COUNT = 20 + __FLEX_NOMINAL_FRAME_COUNT
__EXPECTED_BURST_FRAME_COUNT = 150 + __FLEX_BURST_FRAME_COUNT


def __trex_readfile_worker(file_obj):
    # init
    images = np.array([])
    metadata_dict_list = []
    problematic = False
    error_message = ""
    image_width = 0
    image_height = 0
    image_channels = 0
    image_dtype = np.dtype("uint8")

    # check file extension to know how to process
    try:
        if (file_obj["filename"].endswith("pgm") or file_obj["filename"].endswith("pgm.gz")):
            return __rgb_readfile_worker_pgm(file_obj)
        elif (file_obj["filename"].endswith("png") or file_obj["filename"].endswith("png.tar")):
            return __rgb_readfile_worker_png(file_obj)
        elif (file_obj["filename"].endswith("h5")):
            return __rgb_readfile_worker_h5(file_obj)
        else:
            if (file_obj["quiet"] is False):
                print("Unrecognized file type: %s" % (file_obj["filename"]))
            raise Exception("Unrecognized file type: %s" % ((file_obj["filename"])))
    except Exception as e:
        if (file_obj["quiet"] is False):
            import traceback
            traceback.print_exc()
            print("Failed to process file '%s' " % (file_obj["filename"]))
        problematic = True
        error_message = "failed to process file: %s" % (str(e))
    return images, metadata_dict_list, problematic, file_obj["filename"], error_message, \
        image_width, image_height, image_channels, image_dtype


def __parse_frame_metadata(frame_list):
    # init
    metadata = {}

    # process frame metadata
    for frame_item in frame_list:
        separator_idx = frame_item.find(':')
        key = frame_item[0:separator_idx]
        value = frame_item[(separator_idx + 1):]
        key = key.strip()
        value = value.strip()
        metadata[key] = value

    # return
    return metadata


def __rgb_readfile_worker_h5(file_obj):
    # init
    images = np.array([])
    metadata_dict_list = []
    problematic = False
    error_message = ""
    image_width = 0
    image_height = 0
    image_channels = 0
    image_dtype = __RGB_H5_DT
    nframes = 0

    # open H5 file
    f = h5py.File(file_obj["filename"], 'r')

    # get dataset
    dataset = f["data"]

    # read file metadata
    file_metadata = {}
    frame_keys = []
    for key in dataset.attrs.keys():
        value = dataset.attrs[key]
        if (isinstance(value, np.ndarray) is False):
            file_metadata[key] = value.strip()
        else:
            frame_keys.append(key)

    # check that there's frame metadata
    if (len(frame_keys) == 0):
        problematic = True
        error_message = "No frame metadata exists"
        return images, metadata_dict_list, problematic, file_obj["filename"], error_message, \
            image_width, image_height, image_channels, image_dtype

    # set first frame
    frame_keys = sorted(frame_keys)
    frame_metadata = __parse_frame_metadata(dataset.attrs[frame_keys[0]])
    file_metadata.update(frame_metadata)
    metadata_dict_list.append(file_metadata)

    # set remaining frame metadata
    if (len(frame_keys) >= 2):
        for key in frame_keys[1:]:
            frame_metadata = __parse_frame_metadata(dataset.attrs[key])
            metadata_dict_list.append(frame_metadata)

    # read data
    images = dataset[()]

    # close H5 file
    f.close()

    # set image vars and reshape if multiple images
    if (len(images.shape) == 3):
        # single frame
        nframes = 1
        image_height = images.shape[0]
        image_width = images.shape[1]
        image_channels = images.shape[2]
        images = images.reshape((image_height, image_width, image_channels, 1))
    else:
        # multiple frames
        nframes = images.shape[0]
        image_height = images.shape[1]
        image_width = images.shape[2]
        image_channels = images.shape[3]
        images = images.reshape((image_height, image_width, image_channels, nframes))

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


def __rgb_readfile_worker_png(file_obj):
    # init
    images = np.array([])
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
    if (file_obj["filename"].endswith(".png.tar")):
        # tar file, extract all frames and add to list
        try:
            tf = tarfile.open(file_obj["filename"])
            file_list = sorted(tf.getnames())
            tf.extractall(path=file_obj["tar_tempdir"])
            for i in range(0, len(file_list)):
                file_list[i] = "%s/%s" % (file_obj["tar_tempdir"], file_list[i])
            tf.close()
            is_tar_file = True
        except Exception as e:
            if ("file_list" in locals()):
                # cleanup
                for f in file_list:
                    try:
                        os.remove(f)
                    except Exception:
                        pass
            if (file_obj["quiet"] is False):
                print("Failed to open file '%s' " % (file_obj["filename"]))
            problematic = True
            error_message = "failed to open file: %s" % (str(e))
            return images, metadata_dict_list, problematic, file_obj["filename"], error_message, \
                image_width, image_height, image_channels, image_dtype
    else:
        # regular png
        file_list = [file_obj["filename"]]

    # read each png file
    for f in file_list:
        # process metadata
        try:
            # set metadata values
            file_split = os.path.basename(f).split('_')
            site_uid = file_split[3]
            device_uid = file_split[4]
            exposure = "%.03f ms" % (float(file_split[5][:-2]))
            mode_uid = file_split[6][:-4]

            # set timestamp
            if ("burst" in f):
                timestamp = datetime.datetime.strptime("%sT%s.%s" % (file_split[0], file_split[1], file_split[2]),
                                                       "%Y%m%dT%H%M%S.%f")
            else:
                timestamp = datetime.datetime.strptime("%sT%s" % (file_split[0], file_split[1]),
                                                       "%Y%m%dT%H%M%S")

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
            if (file_obj["quiet"] is False):
                print("Failed to read metadata from file '%s' " % (f))
            problematic = True
            error_message = "failed to read metadata: %s" % (str(e))
            break

        # read png file
        try:
            # read file
            image_np = cv2.imread(f)
            image_height = image_np.shape[0]
            image_width = image_np.shape[1]
            image_channels = image_np.shape[2] if len(image_np.shape) > 2 else 1
            if (image_channels > 1):
                image_matrix = np.reshape(image_np, (image_height, image_width, image_channels, 1))
            else:
                image_matrix = np.reshape(image_np, (image_height, image_width, 1))

            # initialize image stack
            if (first_frame is True):
                images = image_matrix
                first_frame = False
            else:
                if (image_channels > 1):
                    images = np.concatenate([images, image_matrix], axis=3)  # concatenate (on last axis)
                else:
                    images = np.dstack([images, image_matrix])  # depth stack images (on last axis)
        except Exception as e:
            if (file_obj["quiet"] is False):
                print("Failed reading image data frame: %s" % (str(e)))
            metadata_dict_list.pop()  # remove corresponding metadata entry
            problematic = True
            error_message = "image data read failure: %s" % (str(e))
            continue  # skip to next frame

    # remove untarred files
    if (is_tar_file is True):
        for f in file_list:
            os.remove(f)

    # return
    return images, metadata_dict_list, problematic, file_obj["filename"], error_message, \
        image_width, image_height, image_channels, image_dtype


def __rgb_readfile_worker_pgm(file_obj):
    # init
    images = np.array([])
    metadata_dict_list = []
    first_frame = True
    metadata_dict = {}
    site_uid = ""
    device_uid = ""
    problematic = False
    error_message = ""
    image_width = 553
    image_height = 480
    image_channels = 1
    image_dtype = __RGB_PGM_DT

    # Set metadata values
    file_split = os.path.basename(file_obj["filename"]).split('_')
    site_uid = file_split[3]
    device_uid = file_split[4]

    # check file extension to see if it's gzipped or not
    try:
        if file_obj["filename"].endswith("pgm.gz"):
            unzipped = gzip.open(file_obj["filename"], mode='rb')
        elif file_obj["filename"].endswith("pgm"):
            unzipped = open(file_obj["filename"], mode='rb')
        else:
            if (file_obj["quiet"] is False):
                print("Unrecognized file type: %s" % (file_obj["filename"]))
            return images, metadata_dict_list, problematic, file_obj["filename"], error_message, \
                image_width, image_height, image_channels, image_dtype
    except Exception as e:
        if (file_obj["quiet"] is False):
            print("Failed to open file '%s' " % (file_obj["filename"]))
        problematic = True
        error_message = "failed to open file: %s" % (str(e))
        return images, metadata_dict_list, problematic, file_obj["filename"], error_message, \
            image_width, image_height, image_channels, image_dtype

    # read the file
    while True:
        # read a line
        try:
            line = unzipped.readline()
        except Exception as e:
            if (file_obj["quiet"] is False):
                print("Error reading before image data in file '%s'" % (file_obj["filename"]))
            problematic = True
            metadata_dict_list = []
            images = np.array([])
            error_message = "error reading before image data: %s" % (str(e))
            return images, metadata_dict_list, problematic, file_obj["filename"], error_message, \
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
                if (file_obj["quiet"] is False):
                    print("Error decoding metadata line: %s (line='%s', file='%s')" % (str(e), line, file_obj["filename"]))
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
                    metadata_dict[key] = [metadata_dict[key], value]
            else:
                # normal metadata value
                metadata_dict[key] = value

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
                image_np = np.frombuffer(image_bytes, dtype=__RGB_PGM_DT)

                # change 1d numpy array into 480x553 matrix with correctly located pixels
                image_matrix = np.reshape(image_np, (480, 553, 1))
            except Exception as e:
                if (file_obj["quiet"] is False):
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
                images = np.dstack([images, image_matrix])  # depth stack images (on 3rd axis)

    # close gzip file
    unzipped.close()

    # set the site/device uids, or inject the site and device UIDs if they are missing
    if ("Site unique ID" not in metadata_dict):
        metadata_dict["Site unique ID"] = site_uid

    if ("Imager unique ID" not in metadata_dict):
        metadata_dict["Imager unique ID"] = device_uid

    # return
    return images, metadata_dict_list, problematic, file_obj["filename"], error_message, \
        image_width, image_height, image_channels, image_dtype


def read(file_list, workers=1, tar_tempdir=None, quiet=False):
    """
    Read in a single H5 or PNG.tar file, or an array of them. All files
    must be the same type. This also works for reading in PGM or untarred PNG
    files.

    :param file_list: filename or list of filenames
    :type file_list: str
    :param workers: number of worker processes to spawn, defaults to 1
    :type workers: int, optional
    :param tar_tempdir: path to untar to, defaults to '.'
    :type tar_tempdir: str, optional
    :param quiet: reduce output while reading data
    :type quiet: bool, optional

    :return: images, metadata dictionaries, and problematic files
    :rtype: numpy.ndarray, list[dict], list[dict]
    """
    # set tar path
    if (tar_tempdir is None):
        tar_tempdir = Path("%s/.trex_imager_readfile" % (str(Path.home())))

    # set up process pool (ignore SIGINT before spawning pool so child processes inherit SIGINT handler)
    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    pool = Pool(processes=workers)
    signal.signal(signal.SIGINT, original_sigint_handler)  # restore SIGINT handler

    # if input is just a single file name in a string, convert to a list to be fed to the workers
    if isinstance(file_list, str):
        file_list = [file_list]

    # convert to object, injecting other data we need for processing
    processing_list = []
    for f in file_list:
        processing_list.append({
            "filename": f,
            "tar_tempdir": tar_tempdir,
            "quiet": quiet,
        })

    # call readfile function, run each iteration with a single input file from file_list
    pool_data = []
    try:
        pool_data = pool.map(__trex_readfile_worker, processing_list)
    except KeyboardInterrupt:
        pool.terminate()  # gracefully kill children
        return np.empty((0, 0, 0)), [], []
    else:
        pool.close()

    # set sizes
    image_width = pool_data[0][5]
    image_height = pool_data[0][6]
    image_channels = pool_data[0][7]
    image_dtype = pool_data[0][8]

    # set max predicted frame count
    if ("burst" in f):
        predicted_num_frames = len(processing_list) * __EXPECTED_BURST_FRAME_COUNT
    else:
        predicted_num_frames = len(processing_list) * __EXPECTED_NOMINAL_FRAME_COUNT

    # pre-allocate array sizes (optimization)
    if (image_channels > 1):
        images = np.empty([image_height, image_width, image_channels, predicted_num_frames], dtype=image_dtype)
    else:
        images = np.empty([image_height, image_width, predicted_num_frames], dtype=image_dtype)
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
        images = np.delete(images, range(list_position, predicted_num_frames), axis=3)
    else:
        images = np.delete(images, range(list_position, predicted_num_frames), axis=2)

    # ensure entire array views as the dtype
    images = images.astype(image_dtype)

    # return
    pool_data = None
    return images, metadata_dict_list, problematic_file_list
