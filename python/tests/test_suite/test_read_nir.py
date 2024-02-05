import os
import pytest
import numpy as np
import trex_imager_readfile

# globals
DATA_DIR = "%s/data/nir" % (os.path.dirname(os.path.realpath(__file__)))


@pytest.mark.nir
@pytest.mark.parametrize("test_dict", [
    {
        "filename": "20220307_0600_gill_nir-216_8446.pgm.gz",
        "expected_success": True,
        "expected_frames": 10
    },
    {
        "filename": "20220307_0601_gill_nir-216_8446.pgm.gz",
        "expected_success": True,
        "expected_frames": 10
    },
    {
        "filename": "20220307_0605_gill_nir-216_8446.pgm",
        "expected_success": True,
        "expected_frames": 10
    },
])
def test_read_single_file(test_dict):
    # read file
    img, meta, problematic_files = trex_imager_readfile.read_nir("%s/%s" % (DATA_DIR, test_dict["filename"]))

    # check success
    if (test_dict["expected_success"] is True):
        assert len(problematic_files) == 0
    else:
        assert len(problematic_files) > 0

    # check number of frames
    assert img.shape == (256, 256, test_dict["expected_frames"])
    assert len(meta) == test_dict["expected_frames"]

    # check dtype
    assert img.dtype == np.uint16


@pytest.mark.nir
@pytest.mark.parametrize("test_dict", [
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
        ],
        "expected_success": True,
        "expected_frames": 10
    },
    {
        "filenames": [
            "20220307_0605_gill_nir-216_8446.pgm",
        ],
        "expected_success": True,
        "expected_frames": 10
    },
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
            "20220307_0601_gill_nir-216_8446.pgm.gz",
        ],
        "expected_success": True,
        "expected_frames": 20
    },
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
            "20220307_0601_gill_nir-216_8446.pgm.gz",
            "20220307_0605_gill_nir-216_8446.pgm",
        ],
        "expected_success": True,
        "expected_frames": 30
    },
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
            "20220307_0601_gill_nir-216_8446.pgm.gz",
            "20220307_0602_gill_nir-216_8446.pgm.gz",
            "20220307_0603_gill_nir-216_8446.pgm.gz",
            "20220307_0604_gill_nir-216_8446.pgm.gz",
        ],
        "expected_success": True,
        "expected_frames": 50
    },
])
def test_read_multiple_files(test_dict):
    # build file list
    file_list = []
    for f in test_dict["filenames"]:
        file_list.append("%s/%s" % (DATA_DIR, f))

    # read file
    img, meta, problematic_files = trex_imager_readfile.read_nir(file_list)

    # check success
    if (test_dict["expected_success"] is True):
        assert len(problematic_files) == 0
    else:
        assert len(problematic_files) > 0

    # check number of frames
    assert img.shape == (256, 256, test_dict["expected_frames"])
    assert len(meta) == test_dict["expected_frames"]

    # check that there's metadata
    for m in meta:
        assert len(m) > 0

    # check dtype
    assert img.dtype == np.uint16


@pytest.mark.nir
@pytest.mark.parametrize("test_dict", [
    {
        "filename": "20220307_0600_gill_nir-216_8446.pgm.gz",
        "workers": 1,
        "expected_success": True,
        "expected_frames": 10
    },
    {
        "filename": "20220307_0601_gill_nir-216_8446.pgm.gz",
        "workers": 2,
        "expected_success": True,
        "expected_frames": 10
    },
])
def test_read_single_file_workers(test_dict):
    # read file
    img, meta, problematic_files = trex_imager_readfile.read_nir(
        "%s/%s" % (DATA_DIR, test_dict["filename"]),
        workers=test_dict["workers"],
    )

    # check success
    if (test_dict["expected_success"] is True):
        assert len(problematic_files) == 0
    else:
        assert len(problematic_files) > 0

    # check number of frames
    assert img.shape == (256, 256, test_dict["expected_frames"])
    assert len(meta) == test_dict["expected_frames"]

    # check that there's metadata
    for m in meta:
        assert len(m) > 0

    # check dtype
    assert img.dtype == np.uint16


@pytest.mark.nir
@pytest.mark.parametrize("test_dict", [
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
        ],
        "workers": 1,
        "expected_success": True,
        "expected_frames": 10
    },
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
        ],
        "workers": 2,
        "expected_success": True,
        "expected_frames": 10
    },
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
            "20220307_0601_gill_nir-216_8446.pgm.gz",
        ],
        "workers": 1,
        "expected_success": True,
        "expected_frames": 20
    },
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
            "20220307_0601_gill_nir-216_8446.pgm.gz",
        ],
        "workers": 2,
        "expected_success": True,
        "expected_frames": 20
    },
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
            "20220307_0601_gill_nir-216_8446.pgm.gz",
            "20220307_0602_gill_nir-216_8446.pgm.gz",
            "20220307_0603_gill_nir-216_8446.pgm.gz",
            "20220307_0604_gill_nir-216_8446.pgm.gz",
        ],
        "workers": 1,
        "expected_success": True,
        "expected_frames": 50
    },
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
            "20220307_0601_gill_nir-216_8446.pgm.gz",
            "20220307_0602_gill_nir-216_8446.pgm.gz",
            "20220307_0603_gill_nir-216_8446.pgm.gz",
            "20220307_0604_gill_nir-216_8446.pgm.gz",
        ],
        "workers": 2,
        "expected_success": True,
        "expected_frames": 50
    },
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
            "20220307_0601_gill_nir-216_8446.pgm.gz",
            "20220307_0602_gill_nir-216_8446.pgm.gz",
            "20220307_0603_gill_nir-216_8446.pgm.gz",
            "20220307_0604_gill_nir-216_8446.pgm.gz",
        ],
        "workers": 5,
        "expected_success": True,
        "expected_frames": 50
    },
])
def test_read_multiple_files_workers(test_dict):
    # build file list
    file_list = []
    for f in test_dict["filenames"]:
        file_list.append("%s/%s" % (DATA_DIR, f))

    # read file
    img, meta, problematic_files = trex_imager_readfile.read_nir(
        file_list,
        workers=test_dict["workers"],
    )

    # check success
    if (test_dict["expected_success"] is True):
        assert len(problematic_files) == 0
    else:
        assert len(problematic_files) > 0

    # check number of frames
    assert img.shape == (256, 256, test_dict["expected_frames"])
    assert len(meta) == test_dict["expected_frames"]

    # check that there's metadata
    for m in meta:
        assert len(m) > 0

    # check dtype
    assert img.dtype == np.uint16


@pytest.mark.nir
@pytest.mark.parametrize("test_dict", [
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
        ],
        "workers": 1,
        "expected_success": True,
        "expected_frames": 1
    },
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
        ],
        "workers": 2,
        "expected_success": True,
        "expected_frames": 1
    },
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
            "20220307_0601_gill_nir-216_8446.pgm.gz",
        ],
        "workers": 1,
        "expected_success": True,
        "expected_frames": 2
    },
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
            "20220307_0601_gill_nir-216_8446.pgm.gz",
        ],
        "workers": 2,
        "expected_success": True,
        "expected_frames": 2
    },
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
            "20220307_0601_gill_nir-216_8446.pgm.gz",
            "20220307_0605_gill_nir-216_8446.pgm",
        ],
        "workers": 2,
        "expected_success": True,
        "expected_frames": 3
    },
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
            "20220307_0601_gill_nir-216_8446.pgm.gz",
            "20220307_0602_gill_nir-216_8446.pgm.gz",
            "20220307_0603_gill_nir-216_8446.pgm.gz",
            "20220307_0604_gill_nir-216_8446.pgm.gz",
        ],
        "workers": 1,
        "expected_success": True,
        "expected_frames": 5
    },
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
            "20220307_0601_gill_nir-216_8446.pgm.gz",
            "20220307_0602_gill_nir-216_8446.pgm.gz",
            "20220307_0603_gill_nir-216_8446.pgm.gz",
            "20220307_0604_gill_nir-216_8446.pgm.gz",
        ],
        "workers": 2,
        "expected_success": True,
        "expected_frames": 5
    },
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
            "20220307_0601_gill_nir-216_8446.pgm.gz",
            "20220307_0602_gill_nir-216_8446.pgm.gz",
            "20220307_0603_gill_nir-216_8446.pgm.gz",
            "20220307_0604_gill_nir-216_8446.pgm.gz",
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
    img, meta, problematic_files = trex_imager_readfile.read_nir(
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
    assert img.shape == (256, 256, test_dict["expected_frames"])
    assert len(meta) == test_dict["expected_frames"]

    # check that there's metadata
    for m in meta:
        assert len(m) > 0

    # check dtype
    assert img.dtype == np.uint16


@pytest.mark.nir
@pytest.mark.parametrize("test_dict", [
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
        ],
        "workers": 1,
        "expected_success": True,
        "expected_frames": 10
    },
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
            "20220307_0601_gill_nir-216_8446.pgm.gz",
        ],
        "workers": 2,
        "expected_success": True,
        "expected_frames": 20
    },
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
            "20220307_0601_gill_nir-216_8446.pgm.gz",
            "20220307_0605_gill_nir-216_8446.pgm",
        ],
        "workers": 3,
        "expected_success": True,
        "expected_frames": 30
    },
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
            "20220307_0601_gill_nir-216_8446.pgm.gz",
            "20220307_0602_gill_nir-216_8446.pgm.gz",
            "20220307_0603_gill_nir-216_8446.pgm.gz",
            "20220307_0604_gill_nir-216_8446.pgm.gz",
        ],
        "workers": 5,
        "expected_success": True,
        "expected_frames": 50
    },
])
def test_read_no_metadata(test_dict):
    # build file list
    file_list = []
    for f in test_dict["filenames"]:
        file_list.append("%s/%s" % (DATA_DIR, f))

    # read file
    img, meta, problematic_files = trex_imager_readfile.read_nir(
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
    assert img.shape == (256, 256, test_dict["expected_frames"])
    assert len(meta) == test_dict["expected_frames"]

    # check that there's no metadata
    for m in meta:
        assert len(m) == 0

    # check dtype
    assert img.dtype == np.uint16


@pytest.mark.nir
@pytest.mark.parametrize("test_dict", [
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
        ],
        "workers": 1,
        "expected_success": True,
        "expected_frames": 1
    },
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
            "20220307_0601_gill_nir-216_8446.pgm.gz",
        ],
        "workers": 2,
        "expected_success": True,
        "expected_frames": 2
    },
    {
        "filenames": [
            "20220307_0600_gill_nir-216_8446.pgm.gz",
            "20220307_0601_gill_nir-216_8446.pgm.gz",
            "20220307_0602_gill_nir-216_8446.pgm.gz",
            "20220307_0603_gill_nir-216_8446.pgm.gz",
            "20220307_0604_gill_nir-216_8446.pgm.gz",
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
    img, meta, problematic_files = trex_imager_readfile.read_nir(
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
    assert img.shape == (256, 256, test_dict["expected_frames"])
    assert len(meta) == test_dict["expected_frames"]

    # check that there's no metadata
    for m in meta:
        assert len(m) == 0

    # check dtype
    assert img.dtype == np.uint16
