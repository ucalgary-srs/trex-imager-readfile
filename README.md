# TREx All-Sky Imager Raw Data Readfile

![Support languages](https://img.shields.io/badge/Supported%20Languages-IDL%2C%20Python-lightgrey)
![Support platforms](https://img.shields.io/badge/Supported%20Platforms-Windows%2C%20Linux%2C%20Mac-lightgrey)
![MIT License](https://img.shields.io/badge/License-MIT-brightgreen)
[![Support Python versions](https://img.shields.io/badge/Supported%20Python-3.8%20%7C%203.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue)](https://pypi.python.org/pypi/trex-imager-readfile/)
![Supported IDL versions](https://img.shields.io/badge/Supported%20IDL-8.7.2%2B-blue)
[![Python Version](https://img.shields.io/pypi/v/trex-imager-readfile.svg?label=Python%20Package)](https://pypi.python.org/pypi/trex-imager-readfile)
![IDL Version](https://img.shields.io/badge/IDL%20Package-v1.1.1-blue)
[![Github Actions - Tests](https://github.com/ucalgary-aurora/trex-imager-readfile/workflows/tests/badge.svg)](https://github.com/ucalgary-aurora/trex-imager-readfile/actions?query=workflow%3Atests)

This repository contains code for reading Transition Region Explorer (TREx) All-Sky Imager (ASI) raw data. The data can be found at https://data.phys.ucalgary.ca.

Quick Links:
  - [Installation](#installation)
  - [Updating](#updating)
  - [Examples](#examples)
  - [Advanced Installation Methods](#advanced-installation-methods)
  - [Development](#development)

There exists readfile software for both IDL and Python. The datasets supported by these readfiles include:
  - Blueline: [stream0](https://data.phys.ucalgary.ca/sort_by_project/TREx/blueline/stream0) PGM files
  - Near-infrared: [stream0](https://data.phys.ucalgary.ca/sort_by_project/TREx/NIR/stream0) PGM files
  - RGB: [stream0](https://data.phys.ucalgary.ca/sort_by_project/TREx/RGB/stream0) nominal 3s cadence colour images (HDF5), and [stream0.burst](https://data.phys.ucalgary.ca/sort_by_project/TREx/RGB/stream0.burst) 3Hz cadence colour images (PNG)
  - Spectrograph: [stream0](https://data.phys.ucalgary.ca/sort_by_project/TREx/spectrograph/stream0) PGM files

## Installation

This library can be installed for Python or IDL. Python installation is done using `pip` and IDL installation is done using `ipm`.

### Python

The trex-imager-readfile library is available on PyPI and officially supports Python 3.8+.

```console
$ pip install trex-imager-readfile

$ python 
>>> import trex_imager_readfile
```

### IDL

Since IDL 8.7.1, there exists an IDL package manager called [ipm](https://www.l3harrisgeospatial.com/docs/ipm.html#INSTALL). We can use this to install the trex-imager-readfile library with a single command.

1. From the IDL command prompt, run the following:

    ```idl
    IDL> ipm,/install,'https://aurora.phys.ucalgary.ca/public/trex-imager-readfile-idl/latest.zip'
    ```

2. Add the following to your startup file, or run the command manually using the IDL command prompt:

    ```
    [ open your startup.pro file and put the following in it ]
    .run trex_imager_readfile_startup
    ```

3. Reset your IDL session by either clicking the Reset button in the IDL editor or by typing `.reset` into the IDL command prompt. If you compiled the code manually in step 2 (instead of adding to your startup file), skip this step.

For further information, you can view what packages are installed using `ipm,/list`. You can also view the package details using `ipm,/query,'trex-imager-readfile'`. Previous releases are available [here](https://aurora.phys.ucalgary.ca/public/trex-imager-readfile-idl).

## Updating

In Python, `pip` can be used to update the package.

```console
$ pip install --upgrade trex-imager-readfile
```

In IDL, you can use the `ipm` command to update the package.

```idl
IDL> ipm,/update,'trex-imager-readfile'
IDL> .reset

[ instead of resetting, you can recompile manually ]
IDL> .run trex_imager_readfile_startup
```

## Examples

Below are a few quick examples of using the readfile library in Python and IDL.

### Python

Available functions:
  - trex_imager_readfile.read_blueline()
  - trex_imager_readfile.read_nir()
  - trex_imager_readfile.read_rgb()
  - trex_imager_readfile.read_spectrograph()

Example Python notebooks: https://github.com/ucalgary-aurora/trex-imager-readfile/tree/main/python/examples

Further, some quick examples are below.

#### Read a single file

```python
>>> import trex_imager_readfile
>>> filename = "path/to/rgb_data/2022/02/01/fsmi_rgb-01/ut06/20220201_0600_fsmi_rgb-01_full.h5"
>>> img, meta, problematic_files = trex_imager_readfile.read_rgb(filename)
```

#### Read multiple files

```python
>>> import trex_imager_readfile, glob
>>> file_list = glob.glob("path/to/files/2020/01/01/fsmi_rgb-01/ut06/*full.pgm*")
>>> img, meta, problematic_files = trex_imager_readfile.read_rgb(file_list)
```

#### Read using multiple worker processes

```python
>>> import trex_imager_readfile, glob
>>> file_list = glob.glob("path/to/files/2020/01/01/fsmi_rgb-01/ut06/*full.pgm*")
>>> img, meta, problematic_files = trex_imager_readfile.read_rgb(file_list, workers=4)
```

#### Read with no output

If a file has issues being read in, it is placed into the `problematic_files` variable and each error message is written to stdout. If you'd like the read function to not output print messages to stdout, you can use the `quiet=True` parameter.

```python
>>> import trex_imager_readfile, glob
>>> file_list = glob.glob("path/to/files/2020/01/01/fsmi_rgb-01/ut06/*full.pgm*")
>>> img, meta, problematic_files = trex_imager_readfile.read_rgb(file_list, workers=4, quiet=True)
```

### IDL

#### Read a single one-minute file

```
IDL> trex_imager_readfile,filename,img,meta
IDL> help,img
IMG             UINT      = Array[256, 256, 20]
IDL> help,meta
META            STRUCT    = -> TREX_IMAGER_METADATA Array[20]
```

#### Read multiple files (ie. one hour worth)

```
IDL> f=file_search("C:\path\to\files\for\an\hour\*")
IDL> trex_imager_readfile,f,img,meta
IDL> help,img
IMG             UINT      = Array[256, 256, 1200]
IDL> help,meta
META            STRUCT    = -> TREX_IMAGER_METADATA Array[1200]
```

#### Read only the first frame of a file (can be used to speed up performance if you only need the first frame)

```
IDL> trex_imager_readfile,filename,img,meta,/first_frame
IDL> help,img
IMG             UINT      = Array[256, 256]
IDL> help,meta
String          STRUCT    = -> TREX_IMAGER_METADATA
```

#### Read file without processing metadata (file has no metadata or you just don't want to read it)

```
IDL> trex_imager_readfile,filename,img,meta,/no_metadata
```

## Advanced Installation Methods

### IDL

You can alternatively install the trex-imager-readfile library manually by downloading the ZIP file and extracting it into, or adding it to, your IDL path. 

1. Download the latest release [here](https://aurora.phys.ucalgary.ca/public/trex-imager-readfile-idl/latest.zip)
2. Extract the zip file into your IDL path (or add it as a directory to your IDL path)
3. Add the following to your startup file (or run the command manually using the IDL command prompt).

    ```
    [ open your startup.pro file and put the following in it ]
    .run trex_imager_readfile_startup
    ```

4. Reset your IDL session by either clicking the Reset button in the IDL editor or by typing `.reset` into the IDL command prompt.

## Development

### Python 

#### Local development installation

```console
$ git clone https://github.com/ucalgary-aurora/trex-imager-readfile.git
$ cd trex-imager-readfile/python
$ pip install poetry
$ poetry install
```

#### Running test suite

```console
$ cd python
$ make test
[ or do each test separately ]
$ make test-flake8
$ make test-pylint
$ make test-pytest
```

### IDL

#### Preparing a new distributable package

When a new release is ready for deployment, there are a few tasks that need to be done.

1. Increment the version number and change the date in `idlpackage.json`, `trex_imager_readfile.pro`, and `README.md`.
2. Generate a new distributable Zip file ([more info](https://www.l3harrisgeospatial.com/docs/ipm.html#CREATE))

    ```idl
    IDL> ipm,/create,'path_to_code',name='trex-imager-readfile'
    ```

3. Upload the generated Zip file to https://aurora.phys.ucalgary.ca/public/trex-imager-readfile-idl, and update the symlink for latest.zip
