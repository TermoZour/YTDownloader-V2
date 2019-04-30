# TODO - DON'T FORGET ABOUT USER ERRORS
# TODO - USE DICT TO STORE INFO ABOUT SONGS STATE IN PLAYLIST (is_downloaded, is_converted, etc) WITH "PICKLE"
# load playlist url -> get playlist name
# check for history file with name 'playlist name'
# if no history file detected -> create history file and start downloading songs
# if history file detected -> go through file and download what's left
# TODO - ADD MULTI-THREADED PLAYLIST DOWNLOAD - MULTIPROCESS

import argparse
import csv
import os
import urllib
from pprint import pprint
import pickle

import ffmpeg
import googleapiclient.discovery
import httplib2
from pytube import YouTube, exceptions

from apis import YT_SEARCH_API_KEY, SPOTIFY_API_KEY

YT_URL = "https://www.youtube.com/watch?v="
YT_PLAYLIST_URL = "https://www.youtube.com/playlist?list="
DEF_PATH = "downloads"


def download_video(video_url, download_path):
    query = YouTube(video_url)
    stream = query.streams.filter(only_audio=True).order_by("abr").last()

    # check if file is already downloaded
    file = os.path.splitext(os.path.join(
        download_path, stream.default_filename))[0] + ".mp3"
    if os.path.isfile(file):
        print("||ALREADY DOWNLOADED|| ~~ {0}".format(
            stream.default_filename))
        return file
    else:
        # check if download path folder exists
        if not os.path.isdir(download_path):
            os.mkdir(download_path)

        print("||DOWNLOADING|| \"{0}\"\n||DETAILS|| {1}".format(
            query.title, stream))
        file_path = stream.download(output_path=download_path)
        print("||FINISHED|| ~~ \"{0}\"".format(query.title))
        return file_path


def convert_fnc(file_path):
    try:
        if os.path.isfile(file_path):
            if not os.path.splitext(file_path)[1] == ".mp3":
                print("||FOUND FILE|| ~~ {0}".format(file_path))
                stream = ffmpeg.input(file_path)
                stream = ffmpeg.output(stream, file_path.replace(
                    os.path.splitext(file_path)[1], ".mp3"), format="mp3")
                ffmpeg.run(stream)
                os.remove(file_path)
    except FileNotFoundError:
        print("||FILES NOT FOUND||")
        exit(1)
    print("||CONVERSION FINISHED||")


def url_info(video_url):
    query = YouTube(video_url)

    streams = query.streams.filter(only_audio=True).order_by("abr").all()

    print("AUDIO ONLY")
    pprint(streams)

    print("ALL")
    streams = query.streams.all()
    pprint(streams)


def playlist_info(playlist_url):
    youtube = googleapiclient.discovery.build(
        "youtube", "v3", developerKey=YT_SEARCH_API_KEY)

    playlist_request = youtube.playlists().list(
        part="snippet",
        maxResults=50,
        id=playlist_url.replace(YT_PLAYLIST_URL, '')
    )

    items_request = youtube.playlistItems().list(
        part="contentDetails",
        maxResults=50,
        playlistId=playlist_url.replace(YT_PLAYLIST_URL, '')
    )

    playlist_response = playlist_request.execute()
    items_response = items_request.execute()

    return {'title': playlist_response['items'][0]['snippet']['title'],
            'songs': [song["contentDetails"]["videoId"] for song in items_response["items"]]}


def yt_search(words):
    youtube = googleapiclient.discovery.build(
        "youtube", "v3", developerKey=YT_SEARCH_API_KEY)
    try:
        request = youtube.search().list(
            part="snippet",
            regionCode="US",
            maxResults=5,
            order="relevance",
            type="video",
            q=words
        )
        response = request.execute()

        for song in response['items']:
            print(
                "TITLE: {0} \n\
                CHANNEL: {1} \n\
                LINK: {2}\n".format(song['snippet']['title'],
                                    song['snippet']['channelTitle'],
                                    YT_URL + song['id']['videoId']))
        return 0
    except httplib2.ServerNotFoundError:
        print("||COULD NOT CONNECT TO SERVER||")
        print("||MAYBE NO INTERNET CONNECTION||")
        return 1


def csv_read(csv_path):
    with open(csv_path, 'r', newline='') as csv_file:
        reader = csv.DictReader(csv_file)

    search_query = {}
    for row in reader:
        search_query.update(
            {"id": row['#'], "title": row['Title'], "artist": row['Artist'], "spotify-url": row['Spotify URL']})

    return search_query


ap = argparse.ArgumentParser(
    description="Script for downloading YouTube songs and much more.")
group_main = ap.add_mutually_exclusive_group(required=True)
group_main.add_argument("-d", "--url-to-mp3", metavar="url",
                        help="download YouTube video from URL and convert it to .mp3")
group_main.add_argument("-p", "--playlist-to-mp3", metavar="url",
                        help="downloads all songs from YouTube playlist URL and converts them to .mp3")
group_main.add_argument("-i", "--url-info", metavar="url",
                        help="get YouTube video stream data")
group_main.add_argument("-ip", "--playlist-info", metavar="url",
                        help="get YouTube playlist stream data")
group_main.add_argument("-c", "--convert-mp3", metavar="path",
                        help="convert leftover files to .mp3")
group_main.add_argument("-csv", "--convert-csv", metavar="path",
                        help="downloads songs from CSV file and converts them to .mp3")

args = vars(ap.parse_args())

# converts url to mp3 file
if args["url_to_mp3"]:
    url = args["url_to_mp3"]

    if url.startswith(YT_URL):
        print("Using path: {0}".format(DEF_PATH))
        try:
            path = download_video(url, DEF_PATH)

            # now convert the downloaded file
            convert_fnc(path)
        except exceptions.VideoUnavailable:
            print("||VIDEO NOT FOUND||")
            exit(1)
    else:
        print("Wrong URL format!")
        exit(1)
    exit(0)

# converts playlist to list of song URLs then each song to mp3
elif args["playlist_to_mp3"]:
    yt_videos = [{'name': "Slippy - Show Me (feat. Sara Skinner) [Monstercat Lyric Video]",
                  'is_downloaded': False,
                  'is_converted': False,
                  'yt_url': "https://www.youtube.com/watch?v=W58FBW93nRc",
                  'path': "downloads"},
                 {'name': "RIOT - Overkill [Monstercat Release]",
                  'is_downloaded': False,
                  'is_converted': False,
                  'yt-url': "https://www.youtube.com/watch?v=A8pOVirjGF0",
                  'path': "downloads/some_folder"}]
    # create pickle file
    with open('playlist.pickle', 'wb') as pickle_file:
        pickle.dump(yt_videos, pickle_file, protocol=pickle.HIGHEST_PROTOCOL)

    # load pickle file
    with open('playlist.pickle', 'rb') as pickle_file:
        history = pickle.load(pickle_file)

    print("||LOADED FILE||")
    for entry in history:
        if entry['is_downloaded'] is False:
            try:
                # download entry
                entry['is_downloaded'] = True
            except IOError:  # or an actual error, not a placeholder
                print("stuff about error")

        if entry['is_downloaded'] is True and entry['is_converted'] is False:
            try:
                # convert entry
                entry['is_converted'] = True
            except IOError:  # or an actual error, not a placeholder
                print("stuff about error")

    url = args["playlist_to_mp3"]

    if url.startswith(YT_PLAYLIST_URL):
        print("Using default path: {0}".format(DEF_PATH))

        try:
            playlist_info(url)
        except httplib2.ServerNotFoundError:
            print("||COULD NOT CONNECT TO SERVER||")
            print("||MAYBE NO INTERNET CONNECTION||")
            exit(1)

        for video_id in playlist_info(url)['songs']:
            try:
                path = download_video(YT_URL + video_id, DEF_PATH)

                # now convert the downloaded file
                convert_fnc(path)
            except exceptions.VideoUnavailable:
                print("||VIDEO NOT FOUND||")
                exit(1)
    else:
        print("Wrong URL format!")
        exit(1)
    exit(0)

# reads url and prints url stream data
elif args["url_info"]:
    try:
        url_info(args["url_info"])
    except urllib.error.URLError:
        print("||COULD NOT SEARCH URL||")
        print("||MAYBE NO INTERNET CONNECTION||")
        exit(1)
    exit(0)

# reads playlist url and prints video ids
elif args["playlist_info"]:
    url = args["playlist_info"]
    if url.startswith(YT_PLAYLIST_URL):
        try:
            pprint(playlist_info(url))
        except httplib2.ServerNotFoundError:
            print("||COULD NOT CONNECT TO SERVER||")
            print("||MAYBE NO INTERNET CONNECTION||")
            exit(1)
        exit(0)
    else:
        print("Wrong URL format!")
        exit(1)

# converts leftover files to mp3
elif args["convert_mp3"]:
    path = args["convert_mp3"]
    if path == '':
        path = DEF_PATH
        print("Using default path: {0}\n".format(DEF_PATH))
        convert_fnc(DEF_PATH)
        exit(0)
    else:
        print("Download path: {0}\n".format(path))
        convert_fnc(path)
        exit(0)

# reads csv file, searches for the songs on YT then converts them to mp3
elif args["convert_csv"]:
    path = args["convert_csv"]
    print("||OPENING CSV FILE||")
    try:
        csv_read(path)
    except FileNotFoundError:
        print("||CSV FILE NOT FOUND|| ~~ \"{0}\"".format(path))
        exit(1)

    # send songs to the yt_search(words) function
    exit(0)
