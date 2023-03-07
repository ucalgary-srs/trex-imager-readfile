# TREx All-Sky Imager Raw PGM Data Readfile

[![Github Actions - Tests](https://github.com/ucalgary-aurora/trex-imager-readfile/workflows/tests/badge.svg)](https://github.com/ucalgary-aurora/trex-imager-readfile/actions?query=workflow%3Atests)
[![PyPI version](https://img.shields.io/pypi/v/trex-imager-readfile.svg)](https://pypi.python.org/pypi/trex-imager-readfile/)
[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/)
[![PyPI Python versions](https://img.shields.io/badge/python-3.8%20%7C%203.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue)](https://pypi.python.org/pypi/trex-imager-readfile/)

Python library for reading Transition Region Explorer (TREx) All-Sky Imager (ASI) stream0 raw PGM-file data. The data can be found at https://data.phys.ucalgary.ca.

## Supported Datasets

- Blueline: [stream0](https://data.phys.ucalgary.ca/sort_by_project/TREx/blueline/stream0) PGM files
- Near-infrared: [stream0](https://data.phys.ucalgary.ca/sort_by_project/TREx/NIR/stream0) PGM files
- RGB: [stream0](https://data.phys.ucalgary.ca/sort_by_project/TREx/RGB/stream0) single-channel PGM files, [stream0.colour](https://data.phys.ucalgary.ca/sort_by_project/TREx/RGB/stream0.colour) 3-channel PNG files, [stream0.burst](https://data.phys.ucalgary.ca/sort_by_project/TREx/RGB/stream0.burst) 3-channel PNG files
- Spectrograph: [stream0](https://data.phys.ucalgary.ca/sort_by_project/TREx/spectrograph/stream0) PGM files

## Installation

The trex-imager-readfile library is available on PyPI:

```console
$ pip install trex-imager-readfile
```

## Supported Python Versions

trex-imager-readfile officially supports Python 3.8+.

## Examples

Example Python notebooks can be found in the "examples" directory. Further, some examples can be found in the "Usage" section below.

## Usage

Import the library using `import trex_imager_readfile`

### Read a single file

```python
>>> import trex_imager_readfile
>>> filename = "path/to/rgb_data/2020/01/01/fsmi_rgb-01/ut06/20200101_0600_fsmi_rgb-01_full.pgm.gz"
>>> img, meta, problematic_files = trex_imager_readfile.read_rgb(filename)
```

### Read multiple files

```python
>>> import trex_imager_readfile, glob
>>> file_list = glob.glob("path/to/files/2020/01/01/fsmi_rgb-01/ut06/*full.pgm*")
>>> img, meta, problematic_files = trex_imager_readfile.read_rgb(file_list)
```

### Read using multiple worker processes

```python
>>> import trex_imager_readfile, glob
>>> file_list = glob.glob("path/to/files/2020/01/01/fsmi_rgb-01/ut06/*full.pgm*")
>>> img, meta, problematic_files = trex_imager_readfile.read_rgb(file_list, workers=4)
```

### Read with no output

If a file has issues being read in, it is placed into the `problematic_files` variable and each error message is written to stdout. If you'd like the read function to not output print messages to stdout, you can use the `quiet=True` parameter.

```python
>>> import trex_imager_readfile, glob
>>> file_list = glob.glob("path/to/files/2020/01/01/fsmi_rgb-01/ut06/*full.pgm*")
>>> img, meta, problematic_files = trex_imager_readfile.read_rgb(file_list, workers=4, quiet=True)
```

## Development

Clone the repository and install dependencies using Poetry.

```console
$ git clone https://github.com/ucalgary-aurora/trex-imager-readfile.git
$ cd trex-imager-readfile/python
$ make install
```

## Testing

```console
$ make test
[ or do each test separately ]
$ make test-flake8
$ make test-pylint
$ make test-pytest
```
