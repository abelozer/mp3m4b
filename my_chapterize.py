#!/usr/bin/python3

"""
Concatenates mp3 files into single m4b audiobook and adds chapter markers.
"""

import os
import sys
import argparse
import subprocess
import json
import logging
from pathlib import Path
from tqdm import tqdm
from mutagen.mp3 import MP3
from settings import *

file_log_format = "%(asctime)s::%(levelname)s::%(name)s::"\
             "%(filename)s::%(lineno)d::%(message)s"
logging.basicConfig(filename='history.log', level='DEBUG', format=file_log_format)
console_log_format = '%(message)s'
logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')

# Use FileHandler() to log to a file
file_handler = logging.StreamHandler()
formatter = logging.Formatter(console_log_format)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

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
    result = subprocess.check_output([
        "ffprobe",
        file_path,
        "-show_entries",
        "format=duration",
        "-v",
        "quiet",
        "-of",
        "csv=p=0"
    ])
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
    ffprobe_command = [
        "ffprobe",
        str(file_path),
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format"
    ]
    try:
        output = subprocess.check_output(ffprobe_command)
        chapter_text_metadata = output.decode('utf-8')
        json_metadata = json.loads(chapter_text_metadata)
        format_tags = json_metadata.get("format", {}).get("tags", {})
        chapter_title = format_tags.get(tag, "")
        return chapter_title
    except subprocess.CalledProcessError as error:
        logger.error("ffprobe command failed with error: %s", error)
        return ""
    except json.JSONDecodeError as error:
        logger.error("Error decoding JSON metadata: %s", error)
        return ""
    except KeyError as error:
        logger.error("Tag %s not found in metadata: %s", tag, error)
        return ""

def print_metadata(title_length_list: list) -> None:
    """
    Helper function
    """
    for item in title_length_list:
        print(" - ".join(item))

def extract_artwork_from_mp3(artwork_filename: str, folder_path: Path, input_files: list) -> bool:
    """
    Extracts artwork from source mp3 file.
    Takes the first file in the list.
    Returns True if successfull.
    """
    logger.info('Trying to extract artwork from the source mp3 file...')
    shell_command = f"ffmpeg -i '{input_files[0]}' -an -vcodec copy {artwork_filename}"
    os.system(shell_command)
    file_path = os.path.join(folder_path, artwork_filename)
    if os.path.exists(file_path):
        return True
    logger.warning("Unable to extract artwork.")
    return False

def attach_artwork(temp_file: str, artwork_filename: str, output_file_name: str) -> None:
    """
    Attaches artwork to the newly created audiobook file.
    """
    shell_command = f"AtomicParsley '{temp_file}' --artwork {artwork_filename} -o '{output_file_name}.m4b'"
    os.system(shell_command)
    os.remove(temp_file)

def parse_agruments():
    """
    Parses arguments and assignes default values if no arguments provided
    Returns:
        folder_path
        bitrate
        book_title
        artwork_filename
        output_file_name
    """
    parser = argparse.ArgumentParser(description='Concatenates mp3 files and adds chapter markers.')

    # Add arguments to the parser
    parser.add_argument('-p',
                        '--path',
                        type=str,
                        help='Path to folder with mp3 files',
                        default=Path('./'))
    # parser.add_argument('-b',
    #                     '--bitrate',
    #                     type=str,
    #                     help='Bitrate of audiobook  (96k, 128k etc)',
    #                     default=None)
    parser.add_argument('-t',
                        '--title',
                        type=str,
                        help='Audiobook title (tag)',
                        default=None)
    parser.add_argument('-a',
                        '--artwork',
                        type=str,
                        help='Audiobook cover image filename',
                        default=default_artwork_filename)
    parser.add_argument('-o',
                        '--output',
                        type=str,
                        help='Output file name without extension',
                        default="audiobook")

    # Parse the arguments
    args = parser.parse_args()

    # Folder
    if os.path.exists(args.path):
        folder_path = Path(args.path)
        logger.info("Path: %s", folder_path)
    else:
        logger.critical("Path %s does not exist. Exiting", args.path)
        sys.exit()

    # # Bitrate
    # bitrate = args.bitrate
    # logger.info(f'Bitrate: {args.bitrate}')

    # Audiobook title (tag)
    book_title = args.title
    logger.info('Audiobook title: %s', args.title)

    # Checking artwork
    if os.path.exists(args.artwork):
        artwork_filename = args.artwork
        logger.info('Artwork: %s', args.artwork)
    else:
        logger.warning('Artwork: file not found')
        artwork_filename = None

    # Checking output file name
    output_file_name = args.output
    logger.info('Output file name: %s.m4b', args.output)

    # abook = {
    #     "folder_path": folder_path,
    #     "book_title": book_title,
    #     "artwork_filename": artwork_filename,
    #     "output_file_name": output_file_name
    # }
    abook_vars = folder_path, book_title, artwork_filename, output_file_name
    return abook_vars

def get_file_list(folder_path: Path) -> list:
    """
    Get a list of sourse mp3 files
    Args:
        folder_path: folder to search files
    Returns:
        input_files: a sorded list of mp3 files
    """
    # Getting files from source folder
    os.chdir(str(folder_path))
    input_files = sorted(str(file) for file in folder_path.glob('*.mp3'))

    if len(input_files) == 0:
        logger.critical("%s does not contain mp3 files", os.getcwd())
        sys.exit()
    return input_files

def build_title_length_list(input_files: list) -> list:
    """
    Args:
        mp3 file list
    Returns:
        title_length_list: list of lists [filename, chapter_title, chapter_length]
    """
    # Building list with chapters name and length
    title_length_list=[]
    ffprobtime = 0.0 #cummulative start time (nanoseconds)

    for audio_file in tqdm(input_files, desc='Processing mp3 files'):
        chapter_title = get_chapter_title(Path(audio_file), chapter_title_tag)
        if chapter_title == "":
            logger.warning("Unable to get chapter title from %s file", audio_file)
        # ffprobtime += get_length_using_ffprobe(Path(audio_file))
        ffprobtime += get_length_using_mutagen(Path(audio_file))
        title_length_list.append([audio_file, chapter_title, str(int(ffprobtime))])

    return title_length_list

def main():
    """
    Main function
    """

    #logger.basicConfig(filename='history.log', encoding='utf-8', level=logger.DEBUG)

    folder_path, book_title, artwork_filename, output_file_name = parse_agruments()
    input_files = get_file_list(folder_path)
    title_length_list = build_title_length_list(input_files)

    # Getting mp3 file metadata to extract bitrate and book_title
    output = subprocess.run([
        "ffprobe",
        input_files[0],
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format"],
        stdout=subprocess.PIPE,
        universal_newlines=True,
        check=False
        )
    text_metadata = output.stdout
    data = json.loads(text_metadata)
    bitrate = data["format"]["bit_rate"][:-3] + "k"
    tags = data["format"]["tags"]
    if book_title is None:
        if 'album' in tags:
            tags['title']=tags['album']
        else:
            tags['title'] = input("Enter audiobook title tag: ")
    tags['genre']=genre

    # https://ffmpeg.org/ffmpeg-formats.html#Metadata-1
    # "If the timebase is missing then start/end times are assumed to be in 𝗻𝗮𝗻𝗼𝘀𝗲𝗰𝗼𝗻𝗱𝘀."
    # "chapter start and end times in form ‘START=num’, ‘END=num’, where num is a 𝗽𝗼𝘀𝗶𝘁𝗶𝘃𝗲 𝗶𝗻𝘁𝗲𝗴𝗲𝗿."

    with open(ffmetadata_file, 'w', encoding="utf-8") as metafile:
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
        for i in title_length_list:
            print("", file=metafile)
            print("[CHAPTER]", file=metafile)
            print("START=" + start, file=metafile)
            print("END=" + i[2], file=metafile)
            print("title=" + i[1], file=metafile)
            start = str(int(i[2])+1)

    bar_separated_filenames = ''
    for i in input_files:
        bar_separated_filenames += i+'|'

    temp_file = output_file_name + '.m4a'
    shell_command = 'ffmpeg -i "concat:' + bar_separated_filenames[:-1]  + '" -i ' + ffmetadata_file + ' -map_metadata 1 -vn -b:a ' + bitrate + ' \'' + temp_file + '\''
    os.system(shell_command)

    if artwork_filename:
        attach_artwork(temp_file, artwork_filename, output_file_name)
    else:
        if extract_artwork_from_mp3(default_artwork_filename, folder_path, input_files):
            attach_artwork(temp_file, artwork_filename, output_file_name)

    print('\a')

if __name__ == "__main__":
    main()
