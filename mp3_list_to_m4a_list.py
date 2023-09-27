import os

filelist = os.listdir()
mp3_files = [file for file in filelist if file.endswith('.mp3')]
mp3_files.sort()

for file in mp3_files:
    os.system('ffmpeg -i ' + file + ' -vn m4a/' + file.split(".")[0] + '.m4a')
