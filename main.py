# TODO - DON'T FORGET ABOUT USER ERRORS
# TODO - ADD MULTI-THREADED PLAYLIST DOWNLOAD - MULTIPROCESS

import argparse
import csv
import json
import os
import urllib
from pprint import pprint

import ffmpeg
import googleapiclient.discovery
import httplib2
from pytube import YouTube, exceptions, helpers

from apis import YT_SEARCH_API_KEY

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

        print("||DOWNLOADING|| \"{0}\"\n||DETAILS|| {1}\n||PATH|| {2}".format(
            query.title, stream, download_path))
        file_path = stream.download(output_path=download_path)
        print("||FINISHED|| ~~ \"{0}\"".format(query.title))
        return file_path


def convert_fnc(file_path):
    if os.path.isfile(file_path):
        if not os.path.splitext(file_path)[1] == ".mp3":
            print("||FOUND FILE|| ~~ {0}".format(file_path))
            stream = ffmpeg.input(file_path)
            stream = ffmpeg.output(stream, file_path.replace(
                os.path.splitext(file_path)[1], ".mp3"), format="mp3")
            ffmpeg.run(stream)
            os.remove(file_path)


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
        maxResults=1,
        id=playlist_url.replace(YT_PLAYLIST_URL, '')
    )

    items_request = youtube.playlistItems().list(
        part="snippet",
        maxResults=50,
        playlistId=playlist_url.replace(YT_PLAYLIST_URL, '')
    )

    playlist_response = playlist_request.execute()
    items_response = items_request.execute()

    songs = []

    total_results = items_response['pageInfo']['totalResults']

    if total_results <= 50:
        for song in items_response['items']:
            songs.append({'title': song['snippet']['title'], 'id': song['snippet']['resourceId']['videoId']})
    else:
        results = total_results
        while results > 50:
            for song in items_response['items']:
                songs.append({'title': song['snippet']['title'], 'id': song['snippet']['resourceId']['videoId']})

            items_request = youtube.playlistItems().list(
                part="snippet",
                maxResults=50,
                playlistId=playlist_url.replace(YT_PLAYLIST_URL, ''),
                pageToken=items_response['nextPageToken']
            )
            results = total_results - len(songs)
            items_response = items_request.execute()

        for song in items_response['items']:
            songs.append({'title': song['snippet']['title'], 'id': song['snippet']['resourceId']['videoId']})

    return {'playlist_title': playlist_response['items'][0]['snippet']['title'],
            'songs': songs}


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
if args['url_to_mp3']:
    url = args['url_to_mp3']

    if url.startswith(YT_URL):
        print("Using path: {0}".format(DEF_PATH))
        try:
            path = download_video(url, DEF_PATH)

            # now convert the downloaded file
            convert_fnc(path)
        except exceptions.VideoUnavailable:
            print("||VIDEO NOT FOUND||")
            exit(1)
        except urllib.error.HTTPError:
            path = download_video(url, DEF_PATH)

            # now convert the downloaded file
            convert_fnc(path)
    else:
        print("Wrong URL format!")
        exit(1)
    exit(0)

# converts playlist to list of song URLs then each song to mp3
elif args['playlist_to_mp3']:
    url = args['playlist_to_mp3']

    if url.startswith(YT_PLAYLIST_URL):
        try:
            playlist_info(url)
        except httplib2.ServerNotFoundError:
            print("||COULD NOT CONNECT TO SERVER||")
            print("||MAYBE NO INTERNET CONNECTION||")
            exit(1)

        # check for history file to resume unfinished business
        if os.path.isfile(playlist_info(url)['playlist_title'] + '.history'):
            # there is already a file for this playlist
            if os.path.getsize(playlist_info(url)['playlist_title'] + '.history') > 0:
                with open(playlist_info(url)['playlist_title'] + '.history', 'r') as json_file:
                    history = json.load(json_file)

                    if isinstance(history, list):
                        for entry in history:
                            if not all(
                                    keys in entry for keys in ('id', 'title', 'is_downloaded', 'is_converted', 'path')):
                                print("WRONG PLAYLIST HISTORY FILE. \n"
                                      "DELETE THE FILE AND RESTART THE PLAYLIST DOWNLOAD PROCESS")
                                exit(1)

        # history file not created before, so creating now
        else:
            print("||HISTORY FILE NOT FOUND, STARTING FROM BEGINNING||")
            history = []
            for song in playlist_info(url)['songs']:
                path = helpers.safe_filename(playlist_info(url)['playlist_title'])
                history.append({'id': song['id'],
                                'title': song['title'],
                                'is_downloaded': False,
                                'is_converted': False,
                                'path': os.path.join(DEF_PATH, path)})

            with open(playlist_info(url)['playlist_title'] + '.history', 'w') as json_file:
                json.dump(history, json_file)

            with open(playlist_info(url)['playlist_title'] + '.history', 'r') as json_file:
                history = json.load(json_file)

        # processing songs in history file
        for entry in history:
            path = ''
            try:
                if not entry['is_downloaded'] and not entry['is_converted']:
                    path = download_video(YT_URL + entry['id'], entry['path'])
                    entry['is_downloaded'] = True
                    entry['path'] = path

                    # now convert the downloaded file
                    convert_fnc(entry['path'])
                    entry['is_converted'] = True

                    with open(playlist_info(url)['playlist_title'] + '.history', 'w') as json_file:
                        json.dump(history, json_file)
                elif entry['is_downloaded'] and not entry['is_converted']:
                    convert_fnc(entry['path'])
                    entry['is_converted'] = True

                    with open(playlist_info(url)['playlist_title'] + '.history', 'w') as json_file:
                        json.dump(history, json_file)

            except exceptions.VideoUnavailable:
                print("||VIDEO NOT FOUND||")
                exit(1)
            except urllib.error.HTTPError:
                while path == '':
                    print("||ERROR DOWNLOADING SONG. RETRYING.")
                    path = download_video(YT_URL + entry['id'], entry['path'])
                entry['is_downloaded'] = True

                # now convert the downloaded file
                convert_fnc(path)
                entry['is_converted'] = True

                with open(playlist_info(url)['playlist_title'] + '.history', 'w') as json_file:
                    json.dump(history, json_file)
        print("||DONE||")
    else:
        print("Wrong URL format!")
        exit(1)
    exit(0)

# reads url and prints url stream data
elif args['url_info']:
    try:
        url_info(args['url_info'])
    except urllib.error.URLError:
        print("||COULD NOT SEARCH URL||")
        print("||MAYBE NO INTERNET CONNECTION||")
        exit(1)
    exit(0)

# reads playlist url and prints video ids
elif args['playlist_info']:
    url = args['playlist_info']
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
elif args['convert_mp3']:
    path = args['convert_mp3']
    if path == '':
        path = DEF_PATH
        print("Using default path: {0}\n".format(DEF_PATH))
        try:
            convert_fnc(DEF_PATH)
        except FileNotFoundError:
            print("||FILES NOT FOUND||")
            exit(1)
        exit(0)
    else:
        print("Using path: {0}\n".format(path))
        convert_fnc(path)
        exit(0)

# reads csv file, searches for the songs on YT then converts them to mp3
elif args['convert_csv']:
    path = args['convert_csv']
    print("||OPENING CSV FILE||")
    try:
        csv_read(path)
    except FileNotFoundError:
        print("||CSV FILE NOT FOUND|| ~~ \"{0}\"".format(path))
        exit(1)

    # send songs to the yt_search(words) function
    exit(0)
