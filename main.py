# TODO - repeat download in case of error 403 Forbidden
# TODO - DON'T FORGET ABOUT USER ERRORS
# TODO - add file converter (from webm to mp3, etc)

import os
import csv
from pprint import pprint

import ffmpeg
from pytube import YouTube, exceptions

YT_SEARCH_API_KEY = "asdf"
YT_URL = "https://www.youtube.com/watch?v="
DEF_PATH = "downloads"
START_TEXT = """~~~ Python YouTube/Spotify Downloader V2 ~~~
1 - download as mp3
2 - download as mp4
3 - link info
4 - Spotify CSV
5 - convert leftovers
ENTER OPTION: """


# https://www.youtube.com/watch?v=W58FBW93nRc
def download_fnc(url, download_type, download_path):
    if download_type is 0:
        # download as mp3
        try:
            query = YouTube(url)
        except exceptions.VideoUnavailable:
            print("||VIDEO NOT FOUND||")
            return 0
        stream = query.streams.filter(only_audio=True).order_by("abr").last()
        # check if file is already downloaded
        file = os.path.splitext(os.path.join(download_path, stream.default_filename))[0] + ".mp3"
        if os.path.isfile(file):
            print("||ALREADY DOWNLOADED|| ~~ {0}".format(stream.default_filename))
        else:
            # check if download path folder exists
            if not os.path.isdir(download_path):
                os.mkdir(download_path)

            print("||DOWNLOADING|| ~~ \"{0}\"\n||DETAILS|| {1}".format(query.title, stream))
            stream.download(output_path=download_path)
            print("||FINISHED|| ~~ \"{0}\"".format(query.title))
    elif download_type is 2:
        # download as mp4 video - highest quality available
        return 0
    return 0


def convert_fnc(file_path):
    try:
        for filename in os.listdir(file_path):
            file = os.path.join(file_path, filename)
            if os.path.isfile(file):
                if not os.path.splitext(file)[1] == ".mp3":
                    print("||FOUND FILE|| ~~ {0}".format(file))
                    stream = ffmpeg.input(file)
                    stream = ffmpeg.output(stream, file.replace(os.path.splitext(file)[1], ".mp3"), format="mp3")
                    ffmpeg.run(stream)
                    os.remove(file)
    except FileNotFoundError:
        print("||FILES NOT FOUND||")
    print("||CONVERSION FINISHED||")
    return 0


def csv_read(path):
    try:
        with open(path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                print("ID: {0} \nTitle: \"{1}\" \nArtist:\"{2}\" \nSpotify URL: \"{3}\"".format(row['#'], row['Title'], row['Artist'], row['Spotify URL']))
                search_query = row['Title'] + ' - ' + row['Artist']
                print(search_query)
                print('\n')
    except FileNotFoundError:
        print("||CSV FILE NOT FOUND|| ~~ \"{0}\"".format(path))
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

    return 0


# HERE WE GO - START THE ENGINES
while True:
    command = input(START_TEXT)
    # download as mp3
    if command == '1':
        url = input("URL: ")
        if url.startswith(YT_URL):
            path = input("Press enter to use default download path\nPATH: ")
            if path is '':
                print("Using default path: {0}".format(DEF_PATH))
                download_fnc(url, 0, DEF_PATH)
                print('\n')
                # now convert the downloaded file
                convert_fnc(DEF_PATH)
                print('\n')
            else:
                print("Download path: {0}\n".format(path))
                download_fnc(url, 0, path)
                print('\n')
                # now convert the downloaded file
                convert_fnc(path)
                print('\n')
        else:
            print("Wrong URL format!")
        exit(0)
    elif command == '2':
        exit(0)
    # url info
    elif command == '3':
        url_info(input("URL: "))
        exit(0)
    elif command == '4':
        path = os.path.normpath(input("Path to CSV file: "))
        print("||OPENING CSV FILE||")
        csv_read(path)
        exit(0)
    # convert leftovers
    elif command == '5':
        path = input("Press enter to use default download path\nPATH: ")
        if path is '':
            print("Using default path: {0}\n".format(DEF_PATH))
            convert_fnc(DEF_PATH)
            print('\n')
        else:
            print("Download path: {0}\n".format(path))
            convert_fnc(path)
            print('\n')
        exit(0)
    else:
        exit(1)
