; trex_imager_readfile.pro (c) 2020 Darren Chaddock
;
; This program may be freely used, edited, and distributed
; as per the below MIT License. Use at your own risk.
;
; NAME:
;     TREX_IMAGER_READFILE
; VERSION:
;     1.0.0
; PURPOSE:
;     This program is intended to be a general tool for reading
;     Transition Region Explorer (TREx) all-sky camera data.
; EXPLANATION:
;     TREx imager data files are either one-minute stacked binary
;     PGM files, or one-minute tarred PNG files. Metadata is built
;     into the header of the file for the PGM files, and is specified
;     in only the filename in PNG files. This readfile will extract
;     the metadata and image data from a file, returning the data
;     into two variables specified during calling.
;
; CALLING SEQUENCE:
;     TREX_IMAGER_READFILE, filename, images, metadata, /KEYWORDS
; INPUTS:
;     filename  - a string OR array of strings containing valid TREx image filenames
; OUTPUTS:
;     images    - PGM files --> a WIDTH x HEIGHT x NFRAMES array of unsigned integers or bytes
;               - PNG files --> a CHANNELS x WIDTH x HEIGHT x NFRAMES array of unsigned integers or bytes
;     metadata  - a NFRAMES element array of structures
; KEYWORDS:
;     FIRST_FRAME       - only read the first frame of the stacked PGM file or PNG tarball file
;     NO_METADATA       - don't read or process metadata (use if file has no metadata or you don't
;                         want to read it)
;     MINIMAL_METADATA  - set the least required metadata fields (slightly faster)
;     ASSUME_EXISTS     - assume that the filename(s) exist (slightly faster)
;     COUNT             - returns the number of image frames (usage ex. COUNT=nframes)
;     VERBOSE           - set verbosity to level 1
;     VERY_VERBOSE      - set verbosity to level 2
;     SHOW_DATARATE     - show the read datarate stats for each file processed (usually used
;                         with /VERBOSE keyword)
;     UNTAR_DIR         - specify the directory to untar RGB colour PNG files to, default
;                         is 'C:\trex_imager_readfile_working' on Windows and
;                         '~/trex_imager_readfile_working' on Linux (usage
;                         ex. UNTAR_DIR='path\for\files')
;     NO_UNTAR_CLEANUP  - don't remove files after untarring to the UNTAR_DIR and reading
;
; CATEGORY:
;     Image, File reading
;
; USAGE EXAMPLES:
;     1) Read single file
;         IDL> filename = '20200101_0000_gill_nir-01_8446.pgm.gz'
;         IDL> trex_imager_readfile,filename,img,meta
;
;     2) Read list of files
;         IDL> f = file_search('\path\to\trex\nir\data\stream0\2020\01\01\gill_nir-01\ut05\*')
;         IDL> trex_imager_readfile,f,img,meta
;
;     3) Read first frame only
;         IDL> f = file_search('\path\to\trex\nir\data\stream0\2020\01\01\gill_nir-01\ut05\*')
;         IDL> trex_imager_readfile,f,img,meta,/first_frame
;
;     4) Read files without processing the metadata
;         IDL> f = file_search('\path\to\trex\nir\data\stream0\2020\01\01\gill_nir-01\ut05\*')
;         IDL> trex_imager_readfile,f,img,meta,/no_metadata
;
; EXTENDED EXAMPLES:
;     1) Using one file, watch frames as movie
;         IDL> filename = '20200101_0000_gill_nir-01_8446.pgm.gz'
;         IDL> trex_imager_readfile,filename,img,meta,COUNT=nframes
;         IDL> for i=0,nframes-1 DO tvscl,images[*,*,i]
;
;     2) Using 1 hour of data, display as keogram
;         IDL> f = file_search("\path\to\trex\nir\data\stream0\2020\01\01\gill_nir-01\ut05\*"
;         IDL> trex_imager_readfile,f,img,meta,COUNT=nframes,/verbose
;         IDL> keogram = transpose(total(img[96:159,*,*],1))
;         IDL> tvscl,keogram,ORDER=1
;
; NOTES:
;     This code was based on Brian Jackel's "themis_imager_readfile" routine
;     written in 2006. The PGM format is described on the NetPBM home page
;     at http://netpbm.sourceforge.net/doc/pgm.html.
;
; MODIFICATION HISTORY:
;     2020-01-19: Darren Chaddock - creation based on themis_imager_readfile
;
;------------------------
; MIT License
;
; Copyright (c) 2020 University of Calgary
;
; Permission is hereby granted, free of charge, to any person obtaining a copy
; of this software and associated documentation files (the "Software"), to deal
; in the Software without restriction, including without limitation the rights
; to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
; copies of the Software, and to permit persons to whom the Software is
; furnished to do so, subject to the following conditions:
;
; The above copyright notice and this permission notice shall be included in all
; copies or substantial portions of the Software.
;
; THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
; IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
; FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
; AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
; LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
; OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
; SOFTWARE.
;------------------------

; definition for the PBM metadata fields
pro __trex_imager_pbm_metadata__define
  compile_opt HIDDEN
  dummy = {$
    __trex_imager_pbm_metadata,$
    site_uid: '',$
    imager_uid: '',$
    site_latitude: 0.0,$
    site_longitude: 0.0,$
    exposure_start_string: '',$
    exposure_start_cdf: 0.0d0,$
    exposure_duration_request: 0.0,$
    exposure_duration_actual: 0.0,$
    ccd_size: [0,0],$
    ccd_center: [0,0],$
    ccd_offset: [0,0],$
    ccd_binning: [0,0],$
    frame_size: [0,0],$
    comments: ''$
  }
end

; definition for the PNG metadata fields
pro __trex_imager_png_metadata__define
  compile_opt HIDDEN
  dummy = {$
    __trex_imager_png_metadata,$
    site_uid: '',$
    device_uid: '',$
    mode_uid: '',$
    exposure_start_string: '',$
    exposure_start_cdf: 0.0d0,$
    exposure_duration_request: 0.0$
  }
end

pro __trex_cleanup_tar_files,file_list,VERBOSE=verbose
  ; for each file
  if (verbose eq 2) then print,'  Cleaning up untarred files'
  for i=0,n_elements(file_list)-1 do begin
    ; remove file
    file_delete,file_list[i],/ALLOW_NONEXISTENT
  endfor
end

function __trex_png_readfile,filename,image_data,meta_data,dimension_details,n_frames,n_bytes,untar_extract_supported,idl_version_full_support,UNTAR_DIR=untar_dir,NO_UNTAR_CLEANUP=no_untar_cleanup,VERBOSE=verbose,NO_METADATA=no_metadata,FIRST_FRAME=first_frame
  ; init
  compile_opt HIDDEN
  n_frames = 0
  n_bytes = 0
  file_list = []
  cleanup_list = []
  dimension_details = [0, 0, 0]

  ; check if file is tarred
  if (stregex(strupcase(filename),'.*\.TAR$',/BOOLEAN) eq 1) then begin
    ; file is tarred, need to untar it then process each frame
    if (verbose eq 2) then print,'  Untarring tarball: ' + filename
    if (first_frame ne 0) then begin
      ; check that we can do this based on the IDL version
      if (untar_extract_supported eq 0) then begin
        ; file_untar,/extract is not supported --> extract all files
        if (verbose eq 2) then print,"  Warning - TREx RGB png.tar file processing with the /first_frame keyword not supported fully in this IDL version, you'll notice a performance difference in this case. Please use version " + idl_version_full_support + "+"
        file_untar,filename,untar_dir,FILES=untarred_files
        file_list = untarred_files[sort(untarred_files)]
        file_list = file_list[0]
        cleanup_list = untarred_files
      endif else begin
        ; get list of files in tarball
        file_untar,filename,/list,FILES=tar_contents
        if (n_elements(tar_contents) gt 0) then begin
          ; extract just the first one
          tar_contents = tar_contents[sort(tar_contents)]
          file_untar,filename,untar_dir,EXTRACT_FILES=tar_contents[0],FILES=untarred_files
          file_list = [file_list, untarred_files]
          cleanup_list = untarred_files
        endif else begin
          print,'Error - tar file empty'
          goto,ioerror
        endelse
      endelse
    endif else begin
      ; extract all files
      file_untar,filename,untar_dir,FILES=untarred_files
      file_list = [file_list, untarred_files]
      cleanup_list = untarred_files
    endelse
  endif else begin
    ; file is just a png, add to list of files to read
    file_list = [file_list, filename]
    cleanup_list = []
  endelse

  ; for each file
  for i=0,n_elements(file_list)-1 do begin
    ; read png file
    if (verbose eq 2) then print,'  Processing frame: ' + file_basename(file_list[i])
    read_png,file_list[i],frame_img

    ; set dimensions
    image_size = size(frame_img,/STRUCT)
    frame_info = file_info(file_list[i])
    channels = image_size.dimensions[0]
    width = image_size.dimensions[1]
    height = image_size.dimensions[2]
    n_bytes = n_bytes + frame_info.size
    dimension_details = [channels,width,height,image_size.type]

    ; re-orient
    frame_img[0,*,*] = reform(reverse(reform(frame_img[0,*,*]), 2), [1, width, height])
    frame_img[1,*,*] = reform(reverse(reform(frame_img[1,*,*]), 2), [1, width, height])
    frame_img[2,*,*] = reform(reverse(reform(frame_img[2,*,*]), 2), [1, width, height])

    ; allocate memory for image data and metadata if this is the first frame
    if (n_frames eq 0) then begin
      image_data = make_array([channels,width,height,n_elements(file_list)],TYPE=image_size.type,/NOZERO)
      meta_data = replicate({__trex_imager_png_metadata},n_elements(file_list))
    endif

    ; set metadata
    frame_metadata = {__trex_imager_png_metadata}
    if not keyword_set(NO_METADATA) then begin
      basename = file_basename(file_list[i])
      basename_split = strsplit(basename,'_',/extract)
      year = fix(strmid(basename_split[0], 0, 4))
      month = fix(strmid(basename_split[0], 4, 2))
      day = fix(strmid(basename_split[0], 6, 2))
      hour = fix(strmid(basename_split[1], 0, 2))
      minute = fix(strmid(basename_split[1], 2, 2))
      second = fix(strmid(basename_split[1], 4, 2))
      milli = float(basename_split[2])
      frame_metadata.site_uid = basename_split[3]
      frame_metadata.device_uid = basename_split[4]
      frame_metadata.exposure_duration_request = float(strmid(basename_split[5],0,strlen(basename_split[5])-2)) / 1000.0
      mode_uid_split = strsplit(basename_split[6],'.',/extract)
      frame_metadata.mode_uid = mode_uid_split[0]
      frame_metadata.exposure_start_string = '' + strmid(basename_split[0],0,4) + $
        '-' + strmid(basename_split[0],4,2) + '-' + strmid(basename_split[0],6,2) + $
        ' ' + strmid(basename_split[1],0,2) + ':' + strmid(basename_split[1],2,2) + $
        ':' + strmid(basename_split[1],4,2) + '.' + basename_split[2] + ' utc'

      ; set exposure cdf metadata field
      cdf_epoch,epoch,year,month,day,hour,minute,second,milli,/COMPUTE
      frame_metadata.exposure_start_cdf = epoch
    endif

    ; append to image data array
    image_data[0,0,0,n_frames] = frame_img

    ; append to metadata array
    meta_data[n_frames] = frame_metadata

    ; increment number of frames
    n_frames += 1
  endfor

  ; remove extra unused memory
  if (n_frames gt 0 and n_frames lt n_elements(file_list)) then begin
    image_data = image_data[*,*,*,0:n_frames-1]
    meta_data = meta_data[0:n_frames-1]
  endif

  ; cleanup untarred files
  if (no_untar_cleanup eq 0) then __trex_cleanup_tar_files,cleanup_list,VERBOSE=verbose
  return,0

  ; on error, remove extra unused memory, cleanup files, and return
  ioerror:
  print,'Error - could not process PNG file'
  if (n_frames gt 0) then begin
    image_data = image_data[*,*,*,0:n_frames-1]
    meta_data = meta_data[0:n_frames-1]
  endif
  if (no_untar_cleanup eq 0) then __trex_cleanup_tar_files,cleanup_list,VERBOSE=verbose
  return,1
end

function __trex_pbm_readfile,filename,LUN=lun,VERBOSE=verbose,COMMENTS=comments,TUPLE_TYPE=tuple_type,MAXVAL=maxval
  ; set error cases
  if not keyword_set(verbose) then on_error,2
  on_ioerror,ioerror

  ; open file for reading
  if keyword_set(lun) then begin
    ; re-use already acquired lun
    llun = lun
    filename = string(lun,format='("LUN=",I)')
    fs = fstat(llun)
    if (NOT fs.read) then begin
      message,'Error - cannot read from lun ' + string(llun),/INFORMATIONAL
      return,-1L
    endif
  endif else begin
    ; acquire new lun
    f = FINDFILE(filename[0],COUNT=n_files)
    if (n_files eq 0) then begin
      message,'Error - file not found: ' + filename[0],/INFORMATIONAL
      return,-1L
    endif
    compress = stregex(strupcase(filename),'.*\.GZ$',/BOOLEAN)
    openr,llun,f[0],/GET_LUN,/SWAP_if_LITTLE_endIAN,COMPRESS=compress[0]
  endelse

  ; read magic number
  magicnumber = bytarr(2)
  readu,llun,magicnumber
  case string(magicnumber) OF
    'P2':filetype = 2  ;# ASCII grayscale PGM
    'P5':filetype = 5  ;# Binary grayscale PGM
    else: message,'Error - invalid magic number: ' + string(magicnumber)
  endcase

  ; init reading variables
  width = 0
  height = 0
  depth = 0
  maxval = -1L
  tupletype = ''
  depth = ([1,1,3, 1,1,3, 0])[filetype-1]
  line = ''
  comments = ''
  value = lonarr(3)
  nvalues = 0

  ; read file
  repeat begin
    ; read line from lun
    readf,llun,line

    ;check if line is a comment
    pos = strpos(line,'#')
    if (pos ge 0) then begin
      comment = strmid(line,pos+1,999)
      line = strmid(line,0,pos)
    endif else comment = ''
    if (strlen(comment) gt 0) then comments = [comments, comment]

    ; strip off whitespace, if empty then continue to next line
    line = strcompress(strtrim(line,2))
    if (strlen(line) eq 0) then continue

    ; set dimensions
    token = strsplit(line,' ',/EXTRACT)
    ntokens = n_elements(token)
    value[nvalues] = token[0:(ntokens-1)<2]
    nvalues = nvalues + ntokens
  endrep until (nvalues ge 3) or eof(llun)

  ; check if the end of the file was encountered while reading metadata
  if eof(llun) then begin
    if not keyword_set(LUN) then free_lun,llun
    message,'Error - end of file while reading header: ' + filename,/INFORMATIONAL
    return,-1L
  endif

  ; set variables for comments, width, height, bit depth, and max value
  width = value[0]
  height = value[1]
  maxval = value[2]
  if (n_elements(comments) gt 1) then comments = comments[1:*]
  if (width le 0) then begin & message,'Error - invalid width:' + string(width) & return,-1L & endif
  if (height le 0) then begin & message,'Error - invalid height:' + string(height) & return,-1L & endif
  if (depth le 0) then begin & message,'Error - invalid depth:' + string(depth) & return,-1L & endif
  if (maxval le 0) then begin & message,'Error - invalid maxval:' + string(maxval) & return,-1L & endif
  if (maxval gt 65535L) then begin & message,'Error - invalid maxval:' + string(maxval) & return,-1L & endif

  ; set image variable
  if (maxval le 255) then atom = 0b else atom = 0U
  if (depth gt 1) then dimensions = [depth,width,height] else dimensions = [width,height]
  image = replicate(atom,dimensions)

  ; read image data
  if (filetype le 3) then begin
    readf,llun,image
  endif else begin
    readu,llun,image
  endelse

  ; check if we're at the end of the file
  if not keyword_set(lun) then begin
    if (eof(llun) ne 1) then message,'Note - not at end of file',/INFORMATIONAL
    free_lun,llun
  endif

  ; return image
  return,image

  ; on error, free lun
  ioerror:
  free_lun,llun
  print,!ERROR_STATE.MSG
  return,-1L
end

function __trex_imager_parse_pbm_comments,comments,metadata,MINIMAL_METADATA=minimal_metadata
  ; init errors
  on_ioerror,ioerror

  ; init metadata variable
  compile_opt HIDDEN
  metadata = {__trex_imager_pbm_metadata}

  ; set comments field
  metadata.comments = comments[0]
  for i=1,n_elements(comments)-1 do begin
    metadata.comments = metadata.comments + string(13b) + comments[i]
  endfor

  ; set temp variable for processing comments
  tmp = strlowcase(metadata.comments)
  if (strlen(tmp) eq 0) then return,1

  ; set image request start value
  timestring = (stregex(tmp,'"image request start" *([^#]+) utc',/SUBEXPR,/EXTRACT))[1]
  if (timestring eq "") then timestring = (stregex(tmp,'time *([^#]+) *$',/SUBEXPR,/EXTRACT))[1]
  if (timestring eq "") then begin
    message,'Error - could not find time information'
    return,1
  endif
  timestring_split = strsplit(timestring,'"',/extract)
  timestring = strtrim(strmid(timestring_split[0],0,strlen(timestring_split[0])-1))

  ; parse timestring
  year = 0
  month = 0
  day = 0
  hour = 0
  minute = 0
  second = 0.0
  milli = 0.0
  reads,timestring,year,month,day,hour,minute,second,format='(I4,X,I2,X,I2,X,I2,X,I2,X,F9.7)'
  milli = round(1000*(second-fix(second)))
  second = fix(second)

  ; set exposure start string value
  metadata.exposure_start_string = timestring

  ; set exposure start CDF value
  cdf_epoch,epoch,year,month,day,hour,minute,second,milli,/COMPUTE
  metadata.exposure_start_cdf = epoch

  ; if MINIMAL_METADATA keyword is set, then set the values
  if not keyword_set(MINIMAL_METADATA) then begin
    metadata.site_uid = (stregex(tmp,'"site unique *id" ([a-z0-9-]+)',/SUBEXPR,/EXTRACT))[1]
    metadata.imager_uid = (stregex(tmp,'"imager unique *id" ([a-z0-9-]+)',/SUBEXPR,/EXTRACT))[1]
    metadata.site_latitude = (stregex(tmp,'"*latitude" ([a-z0-9-]+.[a-z0-9-]+)',/SUBEXPR,/EXTRACT))[1]
    metadata.site_longitude = (stregex(tmp,'"*longitude" ([a-z0-9-]+.[a-z0-9-]+)',/SUBEXPR,/EXTRACT))[1]
    metadata.ccd_size[0] = (stregex(tmp,'"CCD xsize" ([0-9]+) pixels',/SUBEXPR,/EXTRACT,/FOLD_CASE))[1]
    metadata.ccd_size[1] = (stregex(tmp,'"CCD ysize" ([0-9]+) pixels',/SUBEXPR,/EXTRACT,/FOLD_CASE))[1]
    exposure = stregex(tmp,'"exposure options"[^#]*',/EXTRACT)
    metadata.frame_size = (stregex(exposure,'width=([0-9]+).*height=([0-9]+)',/SUBEXPR,/EXTRACT))[1:2]
    metadata.ccd_offset = (stregex(exposure,'xoffset=([0-9]+).*yoffset=([0-9]+)',/SUBEXPR,/EXTRACT))[1:2]
    metadata.ccd_binning = (stregex(exposure,'xbin=([0-9]+).*ybin=([0-9]+)',/SUBEXPR,/EXTRACT))[1:2]
    metadata.exposure_duration_request = (stregex(exposure,'msec=([0-9]+)',/SUBEXPR,/EXTRACT))[1]
    metadata.exposure_duration_actual = (stregex(tmp,'"exposure.*plus.*readout" *([0-9\.]+) ms',/SUBEXPR,/EXTRACT))[1]

    ; convert exposure milliseconds to seconds
    metadata.exposure_duration_request = metadata.exposure_duration_request / 1d3
    metadata.exposure_duration_actual = metadata.exposure_duration_actual / 1d3
  endif

  ; return success
  return,0

  ; on ioerror, return failure
  ioerror:
  if not keyword_set(NO_METADATA) then begin
    print,'Error - could not read metadata, use /no_metadata keyword to supress this message'
  endif
  metadata = {__trex_imager_pbm_metadata}
  return,1
end

pro trex_imager_readfile,filename,images,metadata,COUNT=n_frames,VERBOSE=verbose,VERY_VERBOSE=very_verbose,SHOW_DATARATE=show_datarate,NO_METADATA=no_metadata,MINIMAL_METADATA=minimal_metadata,ASSUME_EXISTS=assume_exists,FIRST_FRAME=first_frame,UNTAR_DIR=untar_dir,NO_UNTAR_CLEANUP=no_untar_cleanup
  ; init
  stride = 0
  time0 = systime(1)
  filenames = ''
  n_files = 0
  first_call = 1
  n_frames = 0
  n_bytes = 0
  _n_frames = 0
  idl_version_minimum = '8.2.3'
  idl_version_full_support = '8.7.1'
  untar_extract_supported = 1

  ; set keyword flags
  if (n_elements(assume_exists) eq 0) then assume_exists = 0
  if (n_elements(show_datarate) eq 0) then show_datarate = 0
  if (n_elements(no_metadata) eq 0) then no_metadata = 0
  if (n_elements(first_frame) eq 0) then first_frame = 0
  if (n_elements(no_untar_cleanup) eq 0) then no_untar_cleanup = 0

  ; set verbosity
  if (n_elements(verbose) eq 0) then verbose = 0
  if (n_elements(very_verbose) eq 0) then very_verbose = 0
  if (very_verbose ne 0) then verbose = 2

  ; check IDL version
  idl_version = !version.release
  idl_version_split = strsplit(idl_version,'.',/extract)
  idl_version_major = fix(idl_version_split[0])
  idl_version_minor = fix(idl_version_split[1])
  idl_version_micro = fix(idl_version_split[2])
  if (idl_version_major le 7) then begin
    ; too old of a release
    print,'Error - IDL version below 8.2.3 is not supported. You are using version ' + idl_version
    return
  endif else if (idl_version_major eq 8 and idl_version_minor eq 2 and idl_version_micro eq 3) then begin
    ; minimum supported release
    if (verbose eq 2) then print,'Using minimum supported IDL version of 8.2.3, consider upgrading to ' + idl_version_full_support + '+ for all features'
    untar_extract_supported = 0
  endif else if (idl_version_major eq 8 and idl_version_minor le 6) then begin
    ; RGB untarring with /first_frame not supported
    if (verbose eq 2) then begin
      print,'Info - Using IDL version ' + idl_version + ' instead of ' + idl_version_full_support + '+. This version is not fully supported, but, will work for almost all tasks'
    endif
    untar_extract_supported = 0
  endif

  ; set untar directory
  if (n_elements(untar_dir) eq 0) then begin
    ; path not supplied, use default based on OS
    case strlowcase(!version.os_family) of
      'unix': untar_dir = '~/trex_imager_readfile_working'
      'windows': untar_dir = 'C:\trex_imager_readfile_working'
    endcase
  endif else begin
    last_char = strmid(untar_dir,strlen(untar_dir)-1)
    if (last_char eq '/' or last_char eq '\') then begin
      untar_dir = strmid(untar_dir,0,strlen(untar_dir)-1)
    endif
  endelse

  ; init error catching
  catch,error
  if error ne 0 then begin
    print, 'Error: ',!error_state.msg
    return
    catch,/CANCEL
  endif

  ; check if files exist
  if (assume_exists eq 0) then begin
    ; for each filename, check that it exists and is readable
    for i=0,n_elements(filename)-1 do begin
      ; check if file exists and is readable
      file_ok = file_test(filename[i],/READ)
      if (file_ok gt 0) then filenames = [filenames,filename[i]]
    endfor
    n_files = n_elements(filenames)-1
    if (n_files eq 0) then begin
      message,'Error - files not found:' + filename[0],/INFORMATIONAL
      n_frames = 0
      return
    endif
    filenames = filenames[1:n_files]
  endif else begin
    if (n_elements(filename) eq 1) then begin
      filenames = [filename]
    endif
    n_files = n_elements(filenames)
  endelse

  ; sort filenames
  if (n_elements(filenames) gt 1) then filenames = filenames[sort(filenames)]
  if (verbose gt 0) then print,n_elements(filenames),format='("Found ",I," files")'

  ; set values for pre-allocating memory (significantly increases speed)
  n_chunk = 20
  if (stride ne 0) then begin
    n_start = (n_chunk * n_files / stride) < 2400
  endif else begin
    n_start = (n_chunk * n_files) < 2400
  endelse

  ; for each file
  total_expected_frames = 0
  for i=0,n_files-1 do begin
    ; set up error handler
    if (verbose gt 0) then print,' Reading file: ' + filenames[i]
    on_ioerror,fail

    ; determine what type of file (pgm/pgm.gz or png/png.tar)
    if (stregex(strupcase(filenames[i]),'.*\PNG') eq 0) then begin
      ; file is a PNG (either tarred or not), process as RGB file
      processing_mode = 'png'
      ret = __trex_png_readfile(filenames[i],file_images,file_metadata,file_dimension_details,file_nframes,file_total_bytes,untar_extract_supported,idl_version_full_support,UNTAR_DIR=untar_dir,NO_UNTAR_CLEANUP=no_untar_cleanup,VERBOSE=verbose,NO_METADATA=no_metadata,FIRST_FRAME=first_frame)

      ; set images and metadata array
      if (first_call eq 1) then begin
        ; pre-allocate images if it's the first call and we'll be reading more than one file
        if (n_files gt 1) then begin
          ; more than one file will be read, pre-allocate array for all images anticipated to be read in
          total_expected_frames = n_files * file_nframes  ; assume they are all tarballs, array will be trimmed at end
          images = make_array([file_dimension_details[0],file_dimension_details[1],file_dimension_details[2],total_expected_frames],TYPE=file_dimension_details[3],/NOZERO)

          ; insert images
          images[0,0,0,0] = file_images[*,*,*,*]
          metadata = file_metadata
        endif else begin
          ; first call, keep the same images and metadata
          images = file_images
          metadata = file_metadata
        endelse

        ; update first call flag
        first_call = 0
      endif else begin
        ; not the first call, check if the array needs to be expanded
        if ((n_frames+file_nframes) ge total_expected_frames) then begin
          ; need to expand the array
          total_expected_frames = total_expected_frames * 2
          images_new = make_array([file_dimension_details[0],file_dimension_details[1],file_dimension_details[2],total_expected_frames],TYPE=file_dimension_details[3],/NOZERO)
          images_new[0,0,0,0] = images[*,*,*,*]
          images = images_new
        endif

        ; add in new image data and metadata
        images[0,0,0,n_frames] = file_images[*,*,*,*]
        metadata = [metadata,file_metadata]
      endelse

      ; increment number of overall frames and increase n_bytes
      n_frames = n_frames + file_nframes
      n_bytes = n_bytes + file_total_bytes
    endif else begin
      ; file is likely PGM/PGM.GZ, process
      processing_mode = 'pbm'
      openr,lun,filenames[i],/GET_LUN,COMPRESS=stregex(strupcase(filenames[i]),'.*\.GZ$',/BOOLEAN),/SWAP_IF_LITTLE_ENDIAN
      while not eof(lun) do begin
        ; while not the end of the file, process using __trex_pbm_readfile
        if (verbose GE 2) then print,' - reading frame: ' + string(n_frames)
        image = __trex_pbm_readfile(LUN=lun,COMMENTS=comments,VERBOSE=verbose)
        if (image[0] eq -1) then break ; read failure, move on to the next file

        ; increment frame counter
        _n_frames = _n_frames + 1
        if (stride ne 0) then begin
          if (_n_frames mod stride ne 0) then continue
        endif

        ; parse comments
        if (no_metadata eq 0) then begin
          ret = __trex_imager_parse_pbm_comments(comments,mdata,MINIMAL_METADATA=minimal_metadata)
        endif

        ; set returning variables
        if (n_frames eq 0) then begin
          isize = size(image,/STRUCT)
          dimensions = isize.dimensions[0:isize.n_dimensions]
          dimensions[isize.n_dimensions] = n_start
          images = make_array(dimensions,TYPE=isize.type,/NOZERO)
          metadata = replicate({__trex_imager_pbm_metadata},n_start)
          dimensions[isize.n_dimensions] = n_chunk
        endif else if (n_frames ge n_start) then begin
          ; need to expand the arrays
          images = [ [[images]], [[make_array(dimensions,TYPE=isize.type,/NOZERO)]] ]
          metadata = [metadata, replicate({__trex_imager_pbm_metadata},n_chunk)]
          n_start = n_start + n_chunk
        endif

        ; copy previous metadata that may not be present in every record
        if (no_metadata eq 0) then begin
          if (n_frames gt 0) then begin
            mdata.site_uid = metadata[n_frames-1].site_uid
            mdata.imager_uid = metadata[n_frames-1].imager_uid
            mdata.site_latitude = metadata[n_frames-1].site_latitude
            mdata.site_longitude = metadata[n_frames-1].site_longitude
          endif
        endif else begin
          mdata = metadata[n_frames-1]
        endelse

        ; finalize return variables
        metadata[n_frames] = mdata
        images[0,0,n_frames] = image
        n_frames = n_frames + 1

        ; if first_frame keyword is used, then break out
        if (first_frame ne 0) then begin
          break
        endif
      endwhile

      ; increment bytes
      n_bytes = n_bytes + (fstat(lun)).cur_ptr
    endelse

    ; failure point, free the lun
    fail:
    if (isa(lun) eq 1) then free_lun,lun
  endfor

  ; remove extra unused memory
  if (processing_mode eq 'pbm' and n_frames ge 0) then begin
    images = images[*,*,0:n_frames-1]
    metadata = metadata[0:n_frames-1]
  endif else if (processing_mode eq 'png' and n_frames ge 0) then begin
    images = images[*,*,*,0:n_frames-1]
    metadata = metadata[0:n_frames-1]
  endif

  ; show read timing information if verbose keyword is set
  if (show_datarate gt 0) then begin
    dtime = (systime(1) - time0) > 1
    i = 0
    while (n_bytes gt 1024L) do begin
      n_bytes = n_bytes / 1024.0
      i = i + 1
    endwhile
    prefix = (['','K','M','G','T'])[i]
    infoline = string(n_bytes,prefix,dtime,8*n_bytes/dtime,prefix,format='("Read ",F6.1,X,A,"B in ",I," seconds: ",F7.1,X,A,"b/second")')
    print,strcompress(infoline)
  endif
  skip: return
end
