# TREx All-Sky Imager Data Readfile

![version](https://img.shields.io/badge/version-1.0.2-blue)
![idl-required](https://img.shields.io/badge/IDL-8.2.3%2B-lightgrey)
![license](https://img.shields.io/badge/license-MIT-brightgreen)

This repository contains code for reading TREx image data using the IDL programming language. The data can be found at https://data.phys.ucalgary.ca.

## Requirements

- IDL version 8.2.3+ is required, version 8.7.1+ is recommended.
- Windows 7/10, Linux

## Supported Datasets

- Blueline: [stream0](https://data.phys.ucalgary.ca/sort_by_project/TREx/blueline/stream0) PGM files
- Near-infrared: [stream0](https://data.phys.ucalgary.ca/sort_by_project/TREx/NIR/stream0) PGM files
- RGB: [stream0](https://data.phys.ucalgary.ca/sort_by_project/TREx/RGB/stream0) single-channel PGM files, [stream0.colour](https://data.phys.ucalgary.ca/sort_by_project/TREx/RGB/stream0.colour) 3-channel PNG files, [stream0.burst](https://data.phys.ucalgary.ca/sort_by_project/TREx/RGB/stream0.burst) 3-channel PNG files
- Spectrograph: [stream0](https://data.phys.ucalgary.ca/sort_by_project/TREx/spectrograph/stream0) PGM files

## Installation

Download the program "trex_imager_readfile" and include in your IDL Path or compile manually.

## Usage Examples

This readfile can be used in a couple of different ways. Below are a few ways: 

1) read a single file
2) read a list of files
3) read the only the first frame
4) read files without processing the metadata (ie. skip metadata, or you know the file doesn't have any)

### Read a single one-minute file

```
IDL> trex_imager_readfile,filename,img,meta
IDL> help,img
IMG             UINT      = Array[256, 256, 20]
IDL> help,meta
META            STRUCT    = -> TREX_IMAGER_METADATA Array[20]
```

### Read multiple files (ie. one hour worth)

```
IDL> f=file_search("C:\path\to\files\for\an\hour\*")
IDL> trex_imager_readfile,f,img,meta
IDL> help,img
IMG             UINT      = Array[256, 256, 1200]
IDL> help,meta
META            STRUCT    = -> TREX_IMAGER_METADATA Array[1200]
```

### Read only the first frame of a file (can be used to speed up performance if you only need the first frame)

```
IDL> trex_imager_readfile,filename,img,meta,/first_frame
IDL> help,img
IMG             UINT      = Array[256, 256]
IDL> help,meta
String          STRUCT    = -> TREX_IMAGER_METADATA
```

### Read file without processing metadata (file has no metadata or you just don't want to read it)

```
IDL> trex_imager_readfile,filename,img,meta,/no_metadata
```
