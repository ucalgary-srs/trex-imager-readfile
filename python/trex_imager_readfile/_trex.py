# Author: Lukas Vollmerhaus
# Date: 2020-10-16

import gzip as _gzip
import numpy as _np
import signal as _signal
from multiprocessing import Pool as _Pool

# globals
DATA_TYPE = _np.dtype("uint16")
BYTE_ORDER = DATA_TYPE.newbyteorder('>')  # force big endian byte ordering


def read(file_list, workers=1):
    """
    Read in a single PGM or PNG.TAR file, or an array of them. All files
    must be the same type.

    :param file_list: filename or list of filenames
    :type file_list: str
    :param workers: number of worker processes to spawn, defaults to 1
    :type workers: int, optional

    :return: images, metadata dictionaries, and problematic files
    :rtype: numpy.ndarray, list[dict], list[dict]
    """
    # set up process pool (ignore SIGINT before spawning pool so child processes inherit SIGINT handler)
    original_sigint_handler = _signal.signal(_signal.SIGINT, _signal.SIG_IGN)
    pool = _Pool(processes=workers)
    _signal.signal(_signal.SIGINT, original_sigint_handler)  # restore SIGINT handler

    # if input is just a single file name in a string, convert to a list to be fed to the workers
    if isinstance(file_list, str):
        file_list = [file_list]

    # call readfile function, run each iteration with a single input file from file_list
    # NOTE: structure of data - data[file][metadata dictionary lists = 1, images = 0][frame]
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
    expected_frame_count = 20

    # pre-allocate array sizes (optimization)
    predicted_num_frames = len(file_list) * expected_frame_count
    images = _np.empty([image_width, image_height, predicted_num_frames], dtype=DATA_TYPE)
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
        real_num_frames = pool_data[i][0].shape[2]

        # metadata dictionary list at data[][1]
        metadata_dict_list[list_position:list_position + real_num_frames] = pool_data[i][1]
        images[:, :, list_position:list_position + real_num_frames] = pool_data[i][0]  # image arrays at data[][0]
        list_position = list_position + real_num_frames  # advance list position

    # trim unused elements from predicted array sizes
    metadata_dict_list = metadata_dict_list[0:list_position]
    images = _np.delete(images, range(list_position, predicted_num_frames), axis=2)

    # ensure entire array views as uint16
    images = images.astype(_np.uint16)

    # return
    pool_data = None
    return images, metadata_dict_list, problematic_file_list


def __trex_readfile_worker_pgm(file):
    # init
    images = _np.array([])
    metadata_dict_list = []
    first_frame = True
    metadata_dict = {}
    site_uid = ""
    device_uid = ""
    problematic = False
    error_message = ""
    image_width = 0
    image_height = 0

    # open the file
    try:
        if (file.endswith("pgm.gz")):
            unzipped = _gzip.open(file, mode='rb')
        else:
            unzipped = open(file, mode='rb')
    except Exception as e:
        print("Failed to open file '%s' " % (file))
        problematic = True
        error_message = "failed to open file: %s" % (str(e))
        return images, metadata_dict_list, problematic, file, error_message, image_width, image_height

    # read the file
    previous_line = None
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
            return images, metadata_dict_list, problematic, file, error_message, image_width, image_height

        # skip empty lines
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
                previous_line = line
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
            if (key.startswith("Effective image exposure") or key.startswith("Exposure plus readout")):
                metadata_dict_list.append(metadata_dict)
                metadata_dict = {}
        elif line == b'65535\n':
            # there are 2 lines between "exposure plus read out" and the image
            # data, the first is b'256 256\n' and the second is b'65535\n'
            #
            # read image
            try:
                # set the image size based on the previous line
                if (previous_line is None):
                    print("Failed reading image data frame: error getting image dimensions")
                    metadata_dict_list.pop()  # remove corresponding metadata entry
                    problematic = True
                    error_message = "image data read failure: error getting image dimensions"
                    break  # get out
                else:
                    previous_line_split = previous_line.decode("ascii").split(' ')
                    image_width = int(previous_line_split[0])
                    image_height = int(previous_line_split[1])
                    image_num_bytes = image_width * image_height * 2

                # read the image size in bytes from the file
                image_bytes = unzipped.read(image_num_bytes)

                # format bytes into numpy array of unsigned shorts (2byte numbers, 0-65536),
                # effectively an array of pixel values
                image_np = _np.frombuffer(image_bytes, dtype=DATA_TYPE)

                # change 1d numpy array into 256x256 matrix with correctly located pixels
                image_matrix = _np.reshape(image_np, (image_width, image_height, 1))
            except Exception as e:
                print("Failed reading image data frame: %s" % (str(e)))
                metadata_dict_list.pop()  # remove corresponding metadata entry
                problematic = True
                error_message = "image data read failure: %s" % (str(e))
                previous_line = line
                continue  # skip to next frame

            # initialize image stack
            if first_frame:
                images = image_matrix
                first_frame = False
            else:
                images = _np.dstack([images, image_matrix])  # depth stack images (on 3rd axis)

        # set previous line
        previous_line = line

    # close gzip file
    unzipped.close()

    # return
    return images, metadata_dict_list, problematic, file, error_message, image_width, image_height


def __trex_readfile_worker_png(file):
    # init
    pass


def __trex_readfile_worker(file):
    # init
    images = _np.array([])
    metadata_dict_list = []
    problematic = False
    error_message = ""
    image_width = 0
    image_height = 0

    # check file extension to know how to process
    try:
        if (file.endswith("pgm") or file.endswith("pgm.gz")):
            return __trex_readfile_worker_pgm(file)
        elif (file.endswith("png") or file.endswith("png.tar")):
            return __trex_readfile_worker_png(file)
        else:
            print("Unrecognized file type: %s" % (file))
    except Exception as e:
        print("Failed to open file '%s' " % (file))
        problematic = True
        error_message = "failed to open file: %s" % (str(e))
    print("here")
    return images, metadata_dict_list, problematic, file, error_message, image_width, image_height
