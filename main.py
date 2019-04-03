# TODO - repeat download in case of error 403 Forbidden
# TODO - DON'T FORGET ABOUT USER ERRORS
# TODO - add file converter (from webm to mp3, etc)

import csv
import difflib
import os
from pprint import pprint
from subprocess import run

from pytube import YouTube

YT_SEARCH_API_KEY = "asdf"
YT_URL = "http://www.youtube.com/watch?v="
DEF_PATH = "downloads"
START_TEXT = """
1 - download as mp3
2 - download as mp4
3 - link info
"""


def download_fnc(url, download_type):
    if download_type is 1:
        # download as mp3
        query = YouTube(url)
        stream = query.streams.filter(only_audio=True).order_by("abr").last()
        # file_name = stream.default_filename()
        print("Downloading \"{0}\"".format(query.title))
        stream.download()
    elif download_type is 2:
        # download as mp4 video - 1080p
        return 0


def string_to_url(string):
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
    if command == "1":
        download_fnc(input("URL: "), 1)
        exit(0)
    elif command == "2":
        exit(0)
    elif command == "3":
        url_info(input("URL: "))
        exit(0)
    else:
        exit(1)
