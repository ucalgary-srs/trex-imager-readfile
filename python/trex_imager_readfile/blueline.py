import gzip
import numpy as np
import signal
import os
from multiprocessing import Pool
from functools import partial

# globals
__BLUELINE_IMAGE_SIZE_BYTES = 270 * 320 * 2
__BLUELINE_DT = np.dtype("uint16")
__BLUELINE_DT = __BLUELINE_DT.newbyteorder('>')  # force big endian byte ordering


def __blueline_readfile_worker(file, quiet=False):
    # init
    images = np.array([])
    metadata_dict_list = []
    first_frame = True
    metadata_dict = {}
    site_uid = ""
    device_uid = ""
    problematic = False
    error_message = ""

    # set site UID and device UID in case we need it (ie. dark frames, or unstacked files)
    file_split = os.path.basename(file).split('_')
    if (len(file_split) == 5):
        # is a regular file
        site_uid = file_split[2]
        device_uid = file_split[3]
    elif (len(file_split) > 5):
        # is likely a dark frame or a unstacked frame
        site_uid = file_split[3]
        device_uid = file_split[4]

    # check file extension to see if it's gzipped or not
    try:
        if file.endswith("pgm.gz"):
            unzipped = gzip.open(file, mode='rb')
        elif file.endswith("pgm"):
            unzipped = open(file, mode='rb')
        else:
            if (quiet is False):
                print("Unrecognized file type: %s" % (file))
            return images, metadata_dict_list, problematic, file, error_message
    except Exception as e:
        if (quiet is False):
            print("Failed to open file '%s' " % (file))
        problematic = True
        error_message = "failed to open file: %s" % (str(e))
        return images, metadata_dict_list, problematic, file, error_message

    # read the file
    while True:
        # read a line
        try:
            line = unzipped.readline()
        except Exception as e:
            if (quiet is False):
                print("Error reading before image data in file '%s'" % (file))
            problematic = True
            metadata_dict_list = []
            images = np.array([])
            error_message = "error reading before image data: %s" % (str(e))
            return images, metadata_dict_list, problematic, file, error_message

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
                if (quiet is False):
                    print("Error decoding metadata line: %s (line='%s', file='%s')" % (str(e), line, file))
                problematic = True
                error_message = "error decoding metadata line: %s" % (str(e))
                continue

            # split the key and value out of the metadata line
            line_decoded_split = line_decoded.split('"')
            key = line_decoded_split[1]
            value = line_decoded_split[2].strip()

            # add entry to dictionary
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
            if (key.startswith("Exposure plus readout")):
                metadata_dict_list.append(metadata_dict)
                metadata_dict = {}
        elif line == b'65535\n':
            # there are 2 lines between "exposure plus read out" and the image
            # data, the first is b'270 320\n' and the second is b'65535\n'
            #
            # read image
            try:
                # read the image size in bytes from the file
                image_bytes = unzipped.read(__BLUELINE_IMAGE_SIZE_BYTES)

                # format bytes into numpy array of unsigned shorts (2byte numbers, 0-65536),
                # effectively an array of pixel values
                image_np = np.frombuffer(image_bytes, dtype=__BLUELINE_DT)

                # change 1d numpy array into 270x320 matrix with correctly located pixels
                image_matrix = np.reshape(image_np, (270, 320, 1))
            except Exception as e:
                if (quiet is False):
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

    # return
    return images, metadata_dict_list, problematic, file, error_message


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
    predicted_num_frames = len(file_list) * 20
    images = np.empty([270, 320, predicted_num_frames], dtype=__BLUELINE_DT)
    metadata_dict_list = [{}] * predicted_num_frames
    problematic_file_list = []

    # set up process pool (ignore SIGINT before spawning pool so child processes inherit SIGINT handler)
    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    pool = Pool(processes=workers)
    signal.signal(signal.SIGINT, original_sigint_handler)  # restore SIGINT handler

    # if input is just a single file name in a string, convert to a list to be fed to the workers
    if isinstance(file_list, str):
        file_list = [file_list]

    # call readfile function, run each iteration with a single input file from file_list
    # NOTE: structure of data - data[file][metadata dictionary lists = 1, images = 0][frame]
    data = []
    try:
        data = pool.map(partial(__blueline_readfile_worker, quiet=quiet), file_list)
    except KeyboardInterrupt:
        pool.terminate()  # gracefully kill children
        return np.empty((0, 0, 0), dtype=__BLUELINE_DT), [], []
    else:
        pool.close()

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
