# m4b books

## Encode m4a from mp3 files

Simplest way is to concatenate files from a list:

```bash
ffmpeg -f concat -i pathtofilelist outputfilename
```

Later you can add more options:

```bash
ffmpeg -i files.txt -i FFMETADATA_NEW.txt -map_metadata 1 -vn -b:a 96k out.m4a
```

- `-map_metadata 1` says that metadata is in input (-i) number 1.
- `-vn` means no video. It also removes cover image.
- `-acodec copy` says use the same audio stream that's already in there.
- `-b:a 320k` set bitrate for output

`files.txt` example is given below, it can have comments starting with #:

```bash
file '0.mp3'
file '1.mp3'
file '2.mp3'
file '3.mp3'
file '4.mp3'
#file '5.mp3'
#file '6.mp3'
#file '7.mp3'
#file '8.mp3'
#file '9.mp3'
#file '10.mp3'
```

Sometimes you may want to add chaters metadata without re-encoding audio to existing m4a audio file:

```bash
ffmpeg -i source.m4a -i FFMETADATAFILE.txt -map_metadata 1 -codec copy output.m4a
```

FFMETADATA file:

```ini
;FFMETADATA1
title=The toy story
artist=Kathy East Dubovsky
description=Description
genre=Audiobook
album_artist=Name

[CHAPTER]
TIMEBASE=1/1000
START=0
END=951300
title=Глава 1

[CHAPTER]
TIMEBASE=1/1000
START=951300
END=1716000
title=Глава 2

[CHAPTER]
TIMEBASE=1/1000
START=1716000
END=2544200
title=Глава 3

[CHAPTER]
TIMEBASE=1/1000
START=2544200
END=3185500
title=Глава 4

[CHAPTER]
TIMEBASE=1/1000
START=3185500
END=3775000
title=Глава 5

[CHAPTER]
TIMEBASE=1/1000
START=3775000
END=4678500
title=Глава 6

[CHAPTER]
TIMEBASE=1/1000
START=4678500
END=5684000
title=Глава 7

[CHAPTER]
TIMEBASE=1/1000
START=5684000
END=6495500
title=Глава 8

[CHAPTER]
TIMEBASE=1/1000
START=6495500
END=7567500
title=Глава 9

[CHAPTER]
TIMEBASE=1/1000
START=7567500
END=8250200
title=Глава 10

[CHAPTER]
TIMEBASE=1/1000
START=8250200
END=8492716
title=Эпилог
```

## Add artwork

```bash
brew install atomicparsley
AtomicParsley source.m4a --artwork cover.jpg
```

## Find chapters in unlabeled audio

This is where I use Audacity. In Analyse menu select `Label sounds...`. It'll find silence of a defined length.

## Extract artwork

```bash
ffmpeg -i 0.mp3 -an -vcodec copy cover.jpg
```

## Links

'https://ikyle.me/blog/2020/add-mp4-chapters-ffmpeg'

'https://www.terrybutler.co.uk/2021/08/01/how-to-add-chapters-to-video-using-ffmpeg/'

### Using the adelay filter (add silence to beginning)

**Use the [adelay](https://ffmpeg.org/ffmpeg-filters.html#adelay) audio filter if you want to do everything in one command, or if you want to output to a different format than the input (since this method re-encodes anyway). This only works to add silence to the beginning of a file.**

This example will add 1 second of silence to the beginning of a stereo input:

```bash
ffmpeg -i input.flac -af "adelay=1s:all=true" output.opus
```

### Using the apad filter (add silence to the end)

**Use the [apad](https://ffmpeg.org/ffmpeg-filters.html#apad) audio filter if you want to do everything in one command, or if you want to output to a different format than the input (since this method re-encodes anyway). This only works to add silence to the end of a file.**

This example will add 1 second of silence to the end:

```bash
ffmpeg -i input.wav -af "apad=pad_dur=1" output.m4a
```

Add silence in the beginning:

```bash
ffmpeg -i audio_in.wav -af areverse,apad=pad_dur=1s,areverse audio_out.wav
```

Add silence at the end:

```bash
ffmpeg -i audio_in.wav -af apad=pad_dur=1s audio_out.wav
```

Add silence in a loop:

```bash
for i in *.mp3;do ffmpeg -i "$i" -af "apad=pad_dur=1" -b:a 96k "$i".mp3;done
```

TODO: think about making name in the loop above more meaningful.

Sometimes the python code does not help and I have to do it all manually:

1. Remane mp3 files (spaces to underscores)
2. Add 1 sec delay at the end of all mp3 files
3. Concatenate files and include chapters metadata
4. Add cover

```bash
for i in *.mp3;do mv "$i" "${i// /_}";done
for i in *.mp3;do ffmpeg -i "$i" -af "apad=pad_dur=1" -b:a 96k "$i".mp3;done
ffmpeg -f concat -i files.txt -i FFMETADATA_NEW.txt -map_metadata 1 -vn -b:a 96k output.m4a
AtomicParsley output.m4a --artwork ../cover.jpg
```
