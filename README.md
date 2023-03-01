# mp3m4b tool

A small code to build Apple style audiobook from mp3 files and use tags to create chapters.

Prerequisites:
1. ffmpeg
2. ffprobe
3. AtomicParsley
4. mp3 files
5. cover.jpg file in the same folder

Ideally each mp3 file must correspond to a chapter in a new audiobook. Chapter titles are extracted from mp3 tags. Usually the tag used to titles is called `title` but sometimes publishers use another tag and it needs to be reflected in the global variable definition.
