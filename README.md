# TREx Image Data Readfile
![version](https://img.shields.io/badge/version-1.0.0-blue)
![license](https://img.shields.io/badge/license-MIT-brightgreen)
![idl-required](https://img.shields.io/badge/IDL-8.2.3%2B-lightgrey)

This repository contains code for reading TREx image data using the IDL programming language.

## Requirements
- IDL version 8.2.3+
- Windows 7+, Linux

## Installation
Download the program "trex_imager_readfile" and include in your IDL Path or compile manually.

## Usage Examples
This readfile can be used in a couple of different ways: 

1) read in a list of files
2) read in a single file
3) read the first frame of a single file or list of files
4) read files with no metadata
5) read ASCII PGM files (as oppose to Binary PGMs)

### Read a single one-minute file (NIR, Spectrograph, RGB stream0)
<pre>$> f=file_search("C:\path\to\trex\nir\stream0\files\*.pgm*")
$> trex_imager_readfile,f[0],img,meta
$> help,img
IMG             UINT      = Array[256, 256, 10]
$> help,meta
META            STRUCT    = -> TREX_IMAGER_METADATA Array[10]</pre>