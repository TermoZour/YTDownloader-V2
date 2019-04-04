# TODO - repeat download in case of error 403 Forbidden
# TODO - DON'T FORGET ABOUT USER ERRORS
# TODO - add file converter (from webm to mp3, etc)

import os
from pprint import pprint
import ffmpeg

from pytube import YouTube, exceptions

YT_SEARCH_API_KEY = "asdf"
YT_URL = "https://www.youtube.com/watch?v="
DEF_PATH = "downloads/"
START_TEXT = """
1 - download as mp3
2 - download as mp4
3 - link info
4 - convert leftovers
"""

# https://www.youtube.com/watch?v=W58FBW93nRc
def download_fnc(url, download_type, download_path):
    if download_type is 0:
        # download as mp3
        try:
            query = YouTube(url)
        except exceptions.VideoUnavailable:
            print("||Couldn't find video||")

            return 0
        
        stream = query.streams.filter(only_audio=True).order_by("abr").last()
        # check if file is already downloaded
        if os.path.isfile(os.path.join(download_path, stream.default_filename)):
            print("||ALREADY DOWNLOADED|| ~~ {0}".format(stream.default_filename))

            return 0
        else:
            # check if download path folder exists
            if not os.path.isdir(download_path):
                os.mkdir(download_path)

            print("Downloading \"{0}\"".format(query.title))
            stream.download(output_path=download_path)
            print("||FINISHED|| ~~ {0}".format(query.title))

            return 0
    elif download_type is 2:
        # download as mp4 video - highest quality available 
        return 0


def convert_fnc(path):
    for filename in os.listdir(path):
        file = os.path.join(path, filename)
        if os.path.isfile(file):
            print(file)
            # print(ffmpeg.probe(os.path.normpath(file)))
    return 0


def url_info(url):
    query = YouTube(url)
    streams = query.streams.filter(only_audio=True).order_by("abr").all()
    print("AUDIO ONLY")
    pprint(streams)
    print()

    print("ALL")
    streams = query.streams.all()
    pprint(streams)
    print()

# HERE WE GO - START THE ENGINES

while True:
    command = input(START_TEXT)
    if command == '1':
        url = input("URL: ")
        if url.startswith(YT_URL):
            path = os.path.abspath(input("Press enter to use default download path\nPATH: "))
            if path is '':
                print("Using default path: {0}".format(DEF_PATH))
                download_fnc(url, 0, DEF_PATH)
                #now convert the downloaded file
                convert_fnc(DEF_PATH)
            else:
                download_fnc(url, 0, path)
                #now convert the downloaded file
                convert_fnc(path)
        else:
            print("Wrong URL format!")
        exit(0)
    elif command == '2':
        exit(0)
    elif command == '3':
        url_info(input("URL: "))
        exit(0)
    elif command == '4':
        path = input("Press enter to use default download path\nPATH: ")
        if path is '':
            path = os.path.abspath(DEF_PATH)
            print("Using default path: {0}\n".format(path))
            convert_fnc(path)
            exit(0)
        else:
            path = os.path.abspath(path)
            print("Download path: {0}\n".format(path))
            convert_fnc(path)
            print("\n")
            exit(0)
    else:
        exit(1)
