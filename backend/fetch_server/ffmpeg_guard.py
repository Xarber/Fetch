# SPDX-License-Identifier: AGPL-3.0-only
"""Enforce local inputs even if an extractor attempts FFmpeg downloader fallback."""
import os
import sys
from pathlib import Path
from urllib.parse import unquote,urlsplit

LOCAL_PROTOCOLS='file,pipe,crypto,data'

def guarded_arguments(tool,arguments,folder):
    cleaned=[];index=0
    while index<len(arguments):
        arg=arguments[index]
        if arg in ('-protocol_whitelist','-protocol_blacklist'):
            index+=2;continue
        if arg=='-i':
            if index+1>=len(arguments):raise ValueError('Missing input')
            source=arguments[index+1]
            if source not in ('-','pipe:0'):
                parsed=urlsplit(source)
                if parsed.scheme and parsed.scheme!='file':raise ValueError('FFmpeg remote inputs are disabled')
                path=Path(unquote(parsed.path) if parsed.scheme=='file' else source).resolve()
                if not path.is_relative_to(folder.resolve()):raise ValueError('FFmpeg input outside job directory')
            cleaned.extend(['-protocol_whitelist',LOCAL_PROTOCOLS,'-i',source]);index+=2;continue
        cleaned.append(arg);index+=1
    if tool=='ffprobe':cleaned=['-protocol_whitelist',LOCAL_PROTOCOLS]+cleaned
    return cleaned

if __name__=='__main__':
    try:
        tool=sys.argv[1]
        if tool not in ('ffmpeg','ffprobe'):raise ValueError('Unknown tool')
        binary=os.environ['FETCH_REAL_'+tool.upper()]
        args=guarded_arguments(tool,sys.argv[2:],Path(os.environ['FETCH_JOB_DIR']))
        os.execv(binary,[binary,*args])
    except (ValueError,KeyError):
        print('Fetch blocked unsafe media processing input',file=sys.stderr)
        sys.exit(2)
