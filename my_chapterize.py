#!/usr/bin/python3

"""
Concatenates audio files and add chapter markers.
"""

import os
import subprocess
from pathlib import Path
from tqdm import tqdm
import json

folder_path = Path('./')
book_title = ""
output_file = 'out.m4a'
input_audio_files = sorted(str(file) for file in folder_path.glob('*.mp3'))
genre = "Audiobook"
comment = ""
chapter_title_tag = "title"
ffmetadata_file = "FFMETADATA.txt"

def get_length_using_ffprobe(file_path: Path) -> float:
    """
    Get the length of an audio file in nanoseconds using ffprobe.

    Args:
        file_path (Path): The path to the audio file.

    Returns:
        float: The length of the audio file in nanoseconds.
    """
    result = subprocess.check_output(["ffprobe", file_path, "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"])
    ffprobe_length = float(result) * 1e9
    #1.00005
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
    for item in starttimes:
        print(" - ".join(item))

starttimes=[]
ffprobtime = 0.0 #cummulative start time (nanoseconds)
for audio_file in tqdm(input_audio_files, desc='Processing mp3 files'):
    chapter_title = get_chapter_title(Path(audio_file), chapter_title_tag)
    ffprobtime += get_length_using_ffprobe(Path(audio_file))
    starttimes.append([audio_file, chapter_title, str(int(ffprobtime))])

# print_metadata(starttimes)

output = subprocess.run(["ffprobe", input_audio_files[0], "-v", "quiet", "-print_format", "json", "-show_format"], stdout=subprocess.PIPE, universal_newlines=True)
textMetadata = output.stdout
data = json.loads(textMetadata)
tags = data["format"]["tags"]
tags['title']=book_title
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

os.system('ffmpeg -i "concat:' + bar_separated_filenames[:-1]  + '" -i ' + ffmetadata_file + ' -map_metadata 1 -vn -b:a 96k ' + output_file)
os.system('AtomicParsley ' + output_file + ' --artwork cover.jpg -o \'' + book_title + '.m4b\'')
os.remove(output_file)
print('Done!')