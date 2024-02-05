import os
import pytest
import numpy as np
import trex_imager_readfile

# globals
DATA_DIR = "%s/data/rgb/stream0" % (os.path.dirname(os.path.realpath(__file__)))


@pytest.mark.rgb
@pytest.mark.parametrize("test_dict", [
    {
        "filename": "20210205_0600_gill_rgb-04_full.h5",
        "expected_success": True,
        "expected_frames": 20
    },
    {
        "filename": "20210205_0601_gill_rgb-04_full.h5",
        "expected_success": True,
        "expected_frames": 20
    },
])
def test_read_single_file(test_dict):
    # read file
    img, meta, problematic_files = trex_imager_readfile.read_rgb("%s/%s" % (DATA_DIR, test_dict["filename"]))

    # check success
    if (test_dict["expected_success"] is True):
        assert len(problematic_files) == 0
    else:
        assert len(problematic_files) > 0

    # check number of frames
    assert img.shape == (480, 553, 3, test_dict["expected_frames"])
    assert len(meta) == test_dict["expected_frames"]

    # check dtype
    assert img.dtype == np.uint8


@pytest.mark.rgb
@pytest.mark.parametrize("test_dict", [
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
        ],
        "expected_success": True,
        "expected_frames": 20
    },
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
            "20210205_0601_gill_rgb-04_full.h5",
        ],
        "expected_success": True,
        "expected_frames": 40
    },
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
            "20210205_0601_gill_rgb-04_full.h5",
            "20210205_0602_gill_rgb-04_full.h5",
            "20210205_0603_gill_rgb-04_full.h5",
            "20210205_0604_gill_rgb-04_full.h5",
        ],
        "expected_success": True,
        "expected_frames": 100
    },
])
def test_read_multiple_files(test_dict):
    # build file list
    file_list = []
    for f in test_dict["filenames"]:
        file_list.append("%s/%s" % (DATA_DIR, f))

    # read file
    img, meta, problematic_files = trex_imager_readfile.read_rgb(file_list)

    # check success
    if (test_dict["expected_success"] is True):
        assert len(problematic_files) == 0
    else:
        assert len(problematic_files) > 0

    # check number of frames
    assert img.shape == (480, 553, 3, test_dict["expected_frames"])
    assert len(meta) == test_dict["expected_frames"]

    # check that there's metadata
    for m in meta:
        assert len(m) > 0

    # check dtype
    assert img.dtype == np.uint8


@pytest.mark.rgb
@pytest.mark.parametrize("test_dict", [
    {
        "filename": "20210205_0600_gill_rgb-04_full.h5",
        "workers": 1,
        "expected_success": True,
        "expected_frames": 20
    },
    {
        "filename": "20210205_0601_gill_rgb-04_full.h5",
        "workers": 2,
        "expected_success": True,
        "expected_frames": 20
    },
])
def test_read_single_file_workers(test_dict):
    # read file
    img, meta, problematic_files = trex_imager_readfile.read_rgb(
        "%s/%s" % (DATA_DIR, test_dict["filename"]),
        workers=test_dict["workers"],
    )

    # check success
    if (test_dict["expected_success"] is True):
        assert len(problematic_files) == 0
    else:
        assert len(problematic_files) > 0

    # check number of frames
    assert img.shape == (480, 553, 3, test_dict["expected_frames"])
    assert len(meta) == test_dict["expected_frames"]

    # check that there's metadata
    for m in meta:
        assert len(m) > 0

    # check dtype
    assert img.dtype == np.uint8


@pytest.mark.rgb
@pytest.mark.parametrize("test_dict", [
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
        ],
        "workers": 1,
        "expected_success": True,
        "expected_frames": 20
    },
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
        ],
        "workers": 2,
        "expected_success": True,
        "expected_frames": 20
    },
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
            "20210205_0601_gill_rgb-04_full.h5",
        ],
        "workers": 1,
        "expected_success": True,
        "expected_frames": 40
    },
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
            "20210205_0601_gill_rgb-04_full.h5",
        ],
        "workers": 2,
        "expected_success": True,
        "expected_frames": 40
    },
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
            "20210205_0601_gill_rgb-04_full.h5",
            "20210205_0602_gill_rgb-04_full.h5",
            "20210205_0603_gill_rgb-04_full.h5",
            "20210205_0604_gill_rgb-04_full.h5",
        ],
        "workers": 1,
        "expected_success": True,
        "expected_frames": 100
    },
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
            "20210205_0601_gill_rgb-04_full.h5",
            "20210205_0602_gill_rgb-04_full.h5",
            "20210205_0603_gill_rgb-04_full.h5",
            "20210205_0604_gill_rgb-04_full.h5",
        ],
        "workers": 2,
        "expected_success": True,
        "expected_frames": 100
    },
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
            "20210205_0601_gill_rgb-04_full.h5",
            "20210205_0602_gill_rgb-04_full.h5",
            "20210205_0603_gill_rgb-04_full.h5",
            "20210205_0604_gill_rgb-04_full.h5",
        ],
        "workers": 5,
        "expected_success": True,
        "expected_frames": 100
    },
])
def test_read_multiple_files_workers(test_dict):
    # build file list
    file_list = []
    for f in test_dict["filenames"]:
        file_list.append("%s/%s" % (DATA_DIR, f))

    # read file
    img, meta, problematic_files = trex_imager_readfile.read_rgb(
        file_list,
        workers=test_dict["workers"],
    )

    # check success
    if (test_dict["expected_success"] is True):
        assert len(problematic_files) == 0
    else:
        assert len(problematic_files) > 0

    # check number of frames
    assert img.shape == (480, 553, 3, test_dict["expected_frames"])
    assert len(meta) == test_dict["expected_frames"]

    # check that there's metadata
    for m in meta:
        assert len(m) > 0

    # check dtype
    assert img.dtype == np.uint8


@pytest.mark.rgb
@pytest.mark.parametrize("test_dict", [
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
        ],
        "workers": 1,
        "expected_success": True,
        "expected_frames": 1
    },
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
        ],
        "workers": 2,
        "expected_success": True,
        "expected_frames": 1
    },
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
            "20210205_0601_gill_rgb-04_full.h5",
        ],
        "workers": 1,
        "expected_success": True,
        "expected_frames": 2
    },
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
            "20210205_0601_gill_rgb-04_full.h5",
        ],
        "workers": 2,
        "expected_success": True,
        "expected_frames": 2
    },
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
            "20210205_0601_gill_rgb-04_full.h5",
            "20210205_0602_gill_rgb-04_full.h5",
            "20210205_0603_gill_rgb-04_full.h5",
            "20210205_0604_gill_rgb-04_full.h5",
        ],
        "workers": 1,
        "expected_success": True,
        "expected_frames": 5
    },
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
            "20210205_0601_gill_rgb-04_full.h5",
            "20210205_0602_gill_rgb-04_full.h5",
            "20210205_0603_gill_rgb-04_full.h5",
            "20210205_0604_gill_rgb-04_full.h5",
        ],
        "workers": 2,
        "expected_success": True,
        "expected_frames": 5
    },
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
            "20210205_0601_gill_rgb-04_full.h5",
            "20210205_0602_gill_rgb-04_full.h5",
            "20210205_0603_gill_rgb-04_full.h5",
            "20210205_0604_gill_rgb-04_full.h5",
        ],
        "workers": 5,
        "expected_success": True,
        "expected_frames": 5
    },
])
def test_read_first_frame(test_dict):
    # build file list
    file_list = []
    for f in test_dict["filenames"]:
        file_list.append("%s/%s" % (DATA_DIR, f))

    # read file
    img, meta, problematic_files = trex_imager_readfile.read_rgb(
        file_list,
        workers=test_dict["workers"],
        first_frame=True,
    )

    # check success
    if (test_dict["expected_success"] is True):
        assert len(problematic_files) == 0
    else:
        assert len(problematic_files) > 0

    # check number of frames
    assert img.shape == (480, 553, 3, test_dict["expected_frames"])
    assert len(meta) == test_dict["expected_frames"]

    # check that there's metadata
    for m in meta:
        assert len(m) > 0

    # check dtype
    assert img.dtype == np.uint8


@pytest.mark.rgb
@pytest.mark.parametrize("test_dict", [
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
        ],
        "workers": 1,
        "expected_success": True,
        "expected_frames": 20
    },
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
            "20210205_0601_gill_rgb-04_full.h5",
        ],
        "workers": 2,
        "expected_success": True,
        "expected_frames": 40
    },
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
            "20210205_0601_gill_rgb-04_full.h5",
            "20210205_0602_gill_rgb-04_full.h5",
            "20210205_0603_gill_rgb-04_full.h5",
            "20210205_0604_gill_rgb-04_full.h5",
        ],
        "workers": 5,
        "expected_success": True,
        "expected_frames": 100
    },
])
def test_read_no_metadata(test_dict):
    # build file list
    file_list = []
    for f in test_dict["filenames"]:
        file_list.append("%s/%s" % (DATA_DIR, f))

    # read file
    img, meta, problematic_files = trex_imager_readfile.read_rgb(
        file_list,
        workers=test_dict["workers"],
        no_metadata=True,
    )

    # check success
    if (test_dict["expected_success"] is True):
        assert len(problematic_files) == 0
    else:
        assert len(problematic_files) > 0

    # check number of frames
    assert img.shape == (480, 553, 3, test_dict["expected_frames"])
    assert len(meta) == test_dict["expected_frames"]

    # check that there's no metadata
    for m in meta:
        assert len(m) == 0

    # check dtype
    assert img.dtype == np.uint8


@pytest.mark.rgb
@pytest.mark.parametrize("test_dict", [
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
        ],
        "workers": 1,
        "expected_success": True,
        "expected_frames": 1
    },
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
            "20210205_0601_gill_rgb-04_full.h5",
        ],
        "workers": 2,
        "expected_success": True,
        "expected_frames": 2
    },
    {
        "filenames": [
            "20210205_0600_gill_rgb-04_full.h5",
            "20210205_0601_gill_rgb-04_full.h5",
            "20210205_0602_gill_rgb-04_full.h5",
            "20210205_0603_gill_rgb-04_full.h5",
            "20210205_0604_gill_rgb-04_full.h5",
        ],
        "workers": 5,
        "expected_success": True,
        "expected_frames": 5
    },
])
def test_read_first_frame_and_no_metadata(test_dict):
    # build file list
    file_list = []
    for f in test_dict["filenames"]:
        file_list.append("%s/%s" % (DATA_DIR, f))

    # read file
    img, meta, problematic_files = trex_imager_readfile.read_rgb(
        file_list,
        workers=test_dict["workers"],
        first_frame=True,
        no_metadata=True,
    )

    # check success
    if (test_dict["expected_success"] is True):
        assert len(problematic_files) == 0
    else:
        assert len(problematic_files) > 0

    # check number of frames
    assert img.shape == (480, 553, 3, test_dict["expected_frames"])
    assert len(meta) == test_dict["expected_frames"]

    # check that there's no metadata
    for m in meta:
        assert len(m) == 0

    # check dtype
    assert img.dtype == np.uint8
