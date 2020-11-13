# TREx All-Sky Imager Raw PGM Data Readfile

[![Github Actions - Tests](https://github.com/ucalgary-aurora/trex-imager-readfile/workflows/tests/badge.svg)](https://github.com/ucalgary-aurora/trex-imager-readfile/actions?query=workflow%3Atests)
[![PyPI version](https://img.shields.io/pypi/v/trex-imager-readfile.svg)](https://pypi.python.org/pypi/trex-imager-readfile/)
[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/)
[![PyPI Python versions](https://img.shields.io/pypi/pyversions/trex-imager-readfile.svg)](https://pypi.python.org/pypi/trex-imager-readfile/)

Python library for reading Transition Region Explorer (TREx) All-Sky Imager (ASI) stream0 raw PGM-file data. The data can be found at https://data.phys.ucalgary.ca.

## Installation

The trex-imager-readfile library is available on PyPI:

```console
$ python3 -m pip install trex-imager-readfile
```

## Supported Python Versions

trex-imager-readfile officially supports Python 3.6+.

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
