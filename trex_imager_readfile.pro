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
;     images    - a WIDTH x HEIGHT x NFRAMES array of unsigned integers or bytes
;     metadata  - a NFRAMES element array of structures
; KEYWORDS:
;     FIRST_FRAME       - only read the first frame of the stacked PGM file or PNG tarball file
;     NO_METADATA       - don't read or process metadata (use if file has no metadata or you don't want to read it)
;     MINIMAL_METADATA  - set the least required metadata fields (slightly faster)
;     ASSUME_EXISTS     - assume that the filename(s) exist (slightly faster)
;     COUNT             - returns the number of image frames (usage ex. /COUNT=nframes)
;     VERBOSE           - set to increase verbosity
;     SHOW_DATARATE     - show the read datarate stats for each file processed (usually used with /VERBOSE keyword)
;
; CATEGORY:
;     Image, File reading
;
; USAGE EXAMPLES:
;
; EXTENDED EXAMPLES:
;     1) Using one file, watch frames as movie
;           $> filename = "20200101_0000_gill_nir-01_8446.pgm.gz"
;           $> TREX_IMAGER_READFILE,filename,img,meta,COUNT=nframes
;           $> for i=0,nframes-1 DO TVSCL,images[*,*,i]
;
;     2) Using 1 hour of data, display as keogram
;           $> f = file_search("\path\to\trex\nir\data\stream0\2020\01\01\gill_nir-01\ut05\*.pgm*"
;           $> TREX_IMAGER_READFILE,f,img,meta,COUNT=nframes,/VERBOSE
;           $> keogram = TRANSPOSE(TOTAL(img[96:159,*,*],1))
;           $> TVSCL,keogram,ORDER=1
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

; definition for the metadata fields
pro trex_imager_metadata__define
  compile_opt HIDDEN
  dummy = {$
    trex_imager_metadata,$
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

function pam_readfile,filename,LUN=lun,VERBOSE=verbose,COMMENTS=comments,TUPLE_TYPE=tuple_type,MAXVAL=maxval
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
    f = FINDFILE(filename[0],COUNT=nfiles)
    if (nfiles eq 0) then begin
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
    'P3':filetype = 3  ;# ASCII 3-channel colour PPM
    'P5':filetype = 5  ;# Binary grayscale PGM
    'P6':filetype = 6  ;# Binary 3-channel colour PPM
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

function trex_imager_parse_comments,comments,metadata,MINIMAL_METADATA=minimal_metadata
  ; init metadata variable
  compile_opt HIDDEN
  metadata = {trex_imager_metadata}

  ; set comments field
  metadata.comments = comments[0]
  for indx=1,n_elements(comments)-1 do begin
    metadata.comments = metadata.comments + string(13b) + comments[indx]
  endfor

  ; set temp variable for processing comments
  tmp = strlowcase(metadata.comments)
  if (strlen(tmp) eq 0) then return,1
  on_ioerror,ioerror

  ; set image request start value
  timestring = (stregex(tmp,'"image request start" *([^#]+) utc',/SUBEXPR,/EXTRACT))[1]
  if (timestring eq "") then timestring = (stregex(tmp,'time *([^#]+) *$',/SUBEXPR,/EXTRACT))[1]
  if (timestring eq "") then begin
    message,'Error - could not find time information'
    return,1
  endif

  ; set exposure start string value
  metadata.exposure_start_string = timestring

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

  ; on error, return failure
  ioerror:
  return,1
end

pro trex_imager_readfile,filename,images,metadata,COUNT=n_frames,VERBOSE=verbose,SHOW_DATARATE=show_datarate,NO_METADATA=no_metadata,MINIMAL_METADATA=minimal_metadata,ASSUME_EXISTS=assume_exists,FIRST_FRAME=first_frame
  ; init
  stride = 0
  time0 = systime(1)
  filenames = ''
  nfiles = 0

  ; set keyword flags
  if (n_elements(verbose) eq 0) then verbose = 0
  if (n_elements(assume_exists) eq 0) then assume_exists = 0
  if (n_elements(show_datarate) eq 0) then show_datarate = 0
  if (n_elements(no_metadata) eq 0) then no_metadata = 0
  if (n_elements(first_frame) eq 0) then first_frame = 0

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
    nfiles = n_elements(filenames)-1
    if (nfiles eq 0) then begin
      message,'Error - files not found:' + filename[0],/INFORMATIONAL
      n_frames = 0
      return
    endif
    filenames = filenames[1:nfiles]
  endif else begin
    if (n_elements(filename) eq 1) then begin
      filenames = [filename]
    endif
    nfiles = n_elements(filenames)
  endelse

  ; sort filenames
  if (n_elements(filenames) gt 1) then filenames = filenames[sort(filenames)]
  if (verbose gt 0) then print,n_elements(filenames),format='("Found ",I," files")'

  ; set values for pre-allocating memory (significantly increases speed)
  nchunk = 20
  if (stride ne 0) then begin
    nstart = (nchunk * nfiles / stride) < 2400
  endif else begin
    nstart = (nchunk * nfiles) < 2400
  endelse
  n_frames = 0
  n_bytes = 0
  _n_frames = 0

  ; for each file
  for indx=0,nfiles-1 do begin
    ; set up error handler
    if (verbose gt 0) then print,' reading file: ' + filenames[indx]
    on_ioerror,fail

    ; open file
    openr,lun,filenames[indx],/GET_LUN,COMPRESS=stregex(strupcase(filenames[indx]),'.*\.GZ$',/BOOLEAN),/SWAP_IF_LITTLE_ENDIAN
    while not eof(lun) do begin
      ; while not the end of the file, process using pam_readfile
      if (verbose GE 2) then print,' - reading frame: ' + string(n_frames)
      image = pam_readfile(LUN=lun,COMMENTS=comments,VERBOSE=verbose)
      if (image[0] eq -1) then break ; read failure, move on to the next file

      ; increment frame counter
      _n_frames = _n_frames + 1
      if (stride ne 0) then begin
        if (_n_frames mod stride ne 0) then continue
      endif

      ; parse comments
      if (no_metadata eq 0) then begin
        if trex_imager_parse_comments(comments,mdata,MINIMAL_METADATA=minimal_metadata) then break
      endif

      ; set returning variables
      if (n_frames eq 0) then begin
        isize = size(image,/STRUCT)
        dimensions = isize.dimensions[0:isize.n_dimensions]
        dimensions[isize.n_dimensions] = nstart
        images = make_array(dimensions,TYPE=isize.type,/NOZERO)
        metadata = replicate({trex_imager_metadata},nstart)
        dimensions[isize.n_dimensions] = nchunk
      endif else if (n_frames GE nstart) then begin ;need to expand the arrays
        images = [ [[images]], [[make_array(dimensions,TYPE=isize.type,/NOZERO)]] ]
        metadata = [metadata, replicate({trex_imager_metadata},nchunk)]
        nstart = nstart + nchunk
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

    ; failure point, free the lun
    fail:
    free_lun,lun
  endfor

  ; remove extra unused memory
  if (n_frames gt 0) then begin
    metadata = metadata[0:n_frames-1]
    images = images[*,*,0:n_frames-1]
  endif

  ; show read timing information if verbose keyword is set
  if (show_datarate gt 0) then begin
    dtime = (systime(1) - time0) > 1
    indx = 0
    while (n_bytes gt 9*1024L) do begin
      n_bytes = n_bytes / 1024.0
      indx = indx + 1
    endwhile
    prefix = (['','K','M','G','T'])[indx]
    infoline = string(n_bytes,prefix,dtime,8*n_bytes/dtime,prefix,format='(" read ",F6.1,X,A,"B in ",I," seconds: ",F7.1,X,A,"b/second")')
    print,strcompress(infoline)
  endif
  skip: return
end
