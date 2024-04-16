import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from ytmusicapi import YTMusic

ytmusic = YTMusic()

lz_uri = 'spotify:artist:36QJpDe2go2KgaRleHCDTp'
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials("46e21c2eb46e47259c97e9b76435bd05", "04b074f2f7f64542840b7ba605cae0fb"))

results = spotify.artist_top_tracks(lz_uri)

categories = spotify.categories()
genres = categories["categories"]["items"]

music_dataset = []

# genre = genres[5]
# playlistdata = (spotify.category_playlists(genre["id"], limit=5))
# playlists = playlistdata["playlists"]["items"]
# playlist = playlists[2]
# songdata = (spotify.playlist_items(playlist["id"], limit=3))
# songs = songdata["items"]
# song = songs[2]
# if song["track"] != None:
#     print(str(song["track"]["name"] + " By: " + song["track"]["artists"][0]["name"]).encode("utf-8"))
#     search_results = ytmusic.search(song["track"]["name"], filter="songs", limit=10)
#     related = ytmusic.get_watch_playlist(search_results[0]['videoId'], limit=20)
#     print(ytmusic.get_lyrics(related["lyrics"]))

count = 0

for genre in genres:
    print(genre["name"])


for genre in genres:
    playlistdata = (spotify.category_playlists(genre["id"], limit=7))
    playlists = playlistdata["playlists"]["items"]
    if (genre["name"] != "Made For You") & (genre["name"] != "Spotify CLASSICS") & (genre["name"] != "New Releases") & (genre["name"] != "Francophone") & (genre["name"] != "GLOW") & (genre["name"] != "Charts") & (genre["name"] != "Frequency") & (genre["name"] != "Discover") & (genre["name"] != "Decades") & (genre["name"] != "Mood") & (genre["name"] != "Workout") & (genre["name"] != "Indie") & (genre["name"] != "Latin") & (genre["name"] != "Disney"):
        print(genre["name"])
        for playlist in playlists:
            songdata = (spotify.playlist_items(playlist["id"], limit=50))
            songs = songdata["items"]
            for song in songs:
                if song["track"] != None:
                    #print(str(song["track"]["name"] + "       By: " + song["track"]["artists"][0]["name"]).encode("utf-8"))
                    search_results = ytmusic.search(song["track"]["name"], filter="songs", limit=1)

                    if len(search_results) > 0:
                        related = ytmusic.get_watch_playlist(search_results[0]['videoId'], limit=1)
                        lyrics = ""
                        print(count)
                        if related["lyrics"] != None:
                            lyrics = ytmusic.get_lyrics(related["lyrics"])

                            music_dataset.append([song["track"]["name"], song["track"]["artists"][0]["name"], genre["name"], lyrics])
                        count += 1
                            #print("b")

import pandas as pd
df = pd.DataFrame(music_dataset)
df.to_csv("file.csv")


