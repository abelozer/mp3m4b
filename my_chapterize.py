#!/usr/bin/python3

"""
Concatenates mp3 files into single m4b audiobook and adds chapter markers.
"""

import os
import sys
import argparse
import subprocess
import json
from pathlib import Path
from tqdm import tqdm
from mutagen.mp3 import MP3

parser = argparse.ArgumentParser(description='Concatenates audio files and adds chapter markers.')

# Add arguments to the parser
parser.add_argument('-p', '--path', type=str, help='Path to folder with mp3 files')
parser.add_argument('-b', '--bitrate', type=str, help='Bitrate of audiobook  (96k, 128k etc)')
parser.add_argument('-t', '--title', type=str, help='Audiobook title')
parser.add_argument('-a', '--artwork', type=str, help='Audiobook cover image')
parser.add_argument('-o', '--output', type=str, help='Output file name without extension')

# Parse the arguments
args = parser.parse_args()

if args.path:
    folder_path = Path(args.path)
    print(f"Path: {folder_path}")
else:
    folder_path = Path('./')
    print("Path: trying current folder")
if args.bitrate:
    bitrate = args.bitrate
    print(f'Bitrate: {args.bitrate}')
else:
    bitrate = ""
    print('Default bitrate: we\'ll try to get it from mp3 files')
if args.title:
    book_title = args.title
    print(f'Title: {args.title}')
else:
    book_title = ""
    print('Default title: we\'ll try to get it from mp3 tag Album')
if args.artwork:
    artwork_filename = args.artwork
    print(f'Artwork: {args.artwork}')
else:
    artwork_filename = "cover.jpg"
    print(f'Default Artwork: {artwork_filename}')
if args.output:
    output_file_name = args.output
    print(f'Output file name: {args.output}.m4b')
else:
    output_file_name = "audiobook"
    print(f'Default output file name: {output_file_name}.m4b')

os.chdir(str(folder_path))
input_audio_files = sorted(str(file) for file in folder_path.glob('*.mp3'))

if len(input_audio_files) == 0:
    print(f"{os.getcwd()} does not contain mp3 files")
    sys.exit()
genre = "Audiobook"
comment = ""
chapter_title_tag = "title"
ffmetadata_file = "FFMETADATA.txt"

def get_length_using_mutagen(file_path: Path) -> float:
    """
    Get the length of an audio file in nanoseconds using mutagen lib.

    Args:
        file_path (Path): The path to the audio file.

    Returns:
        float: The length of the audio file in nanoseconds.
    """
    audio = MP3(file_path)
    mutagen_length = float(audio.info.length) * 1e9 * 1.0002
    return mutagen_length

def get_length_using_ffprobe(file_path: Path) -> float:
    """
    Get the length of an audio file in nanoseconds using ffprobe.

    Args:
        file_path (Path): The path to the audio file.

    Returns:
        float: The length of the audio file in nanoseconds.
    """
    result = subprocess.check_output(["ffprobe", file_path, "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"])
    ffprobe_length = float(result) * 1e9 * 1.0005
    #1.0001
    return ffprobe_length

def get_chapter_title(file_path: Path, tag: str) -> str:
    """
    Get the title of the chapter from the audio file's metadata using ffprobe.

    Args:
        file_path (Path): The path to the audio file.
        tag (str): The metadata tag to search for.

    Returns:
        str: The title of the chapter.
    """
    output = subprocess.check_output(["ffprobe", file_path, "-v", "quiet", "-print_format", "json", "-show_format"])
    chapter_text_metadata = output.decode('utf-8')
    json_metadata = json.loads(chapter_text_metadata)
    chapter_title = json_metadata["format"]["tags"][tag]
    return chapter_title

def print_metadata(starttimes: list) -> None:
    """
    Helper function
    """
    for item in starttimes:
        print(" - ".join(item))

starttimes=[]
ffprobtime = 0.0 #cummulative start time (nanoseconds)
for audio_file in tqdm(input_audio_files, desc='Processing mp3 files'):
    chapter_title = get_chapter_title(Path(audio_file), chapter_title_tag)
    # ffprobtime += get_length_using_ffprobe(Path(audio_file))
    ffprobtime += get_length_using_mutagen(Path(audio_file))
    starttimes.append([audio_file, chapter_title, str(int(ffprobtime))])

output = subprocess.run(["ffprobe", input_audio_files[0], "-v", "quiet", "-print_format", "json", "-show_format"], stdout=subprocess.PIPE, universal_newlines=True)
textMetadata = output.stdout
data = json.loads(textMetadata)
if bitrate == "":
    bitrate = data["format"]["bit_rate"][:-3] + "k"
tags = data["format"]["tags"]
if book_title == "":
    if 'album' in tags:
        tags['title']=tags['album']
    else:
        tags['title'] = "Audiobook"
tags['genre']=genre

# https://ffmpeg.org/ffmpeg-formats.html#Metadata-1
# "If the timebase is missing then start/end times are assumed to be in 𝗻𝗮𝗻𝗼𝘀𝗲𝗰𝗼𝗻𝗱𝘀."
# "chapter start and end times in form ‘START=num’, ‘END=num’, where num is a 𝗽𝗼𝘀𝗶𝘁𝗶𝘃𝗲 𝗶𝗻𝘁𝗲𝗴𝗲𝗿."

with open(ffmetadata_file, 'w') as metafile:
    print(";FFMETADATA1", file=metafile)
    print("title=" + tags['title'], file=metafile)
    print("comment=" + comment, file=metafile)
    if 'artist' in tags:
        print("artist=" + tags['artist'], file=metafile)
    if 'album_artist' in tags:
        print("album_artist=" +tags['album_artist'], file=metafile)
    print("genre=" + tags['genre'], file=metafile)
    if 'date' in tags:
        print("date=" + tags['date'], file=metafile)
    if 'publisher' in tags:
        print("publisher=" + tags['publisher'], file=metafile)
    start = "0"
    for i in starttimes:
        print("", file=metafile)
        print("[CHAPTER]", file=metafile)
        print("START=" + start, file=metafile)
        print("END=" + i[2], file=metafile)
        print("title=" + i[1], file=metafile)
        start = str(int(i[2])+1)

bar_separated_filenames = ''
for i in input_audio_files:
    bar_separated_filenames += i+'|'

temp_file = output_file_name + '.m4a'
os.system('ffmpeg -i "concat:' + bar_separated_filenames[:-1]  + '" -i ' + ffmetadata_file + ' -map_metadata 1 -vn -b:a ' + bitrate + ' \'' + temp_file + '\'')
if os.path.isfile(artwork_filename):
    os.system('AtomicParsley ' + temp_file + ' --artwork ' + artwork_filename + ' -o \'' + output_file_name + '.m4b\'')
    os.remove(temp_file)
else:
    print(f"{artwork_filename} does not exist.")
print('\a')
print('Done!')
