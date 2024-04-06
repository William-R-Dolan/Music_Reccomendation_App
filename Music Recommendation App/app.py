from flask import Flask, render_template, request
from ytmusicapi import YTMusic

from urllib.request import urlopen

app = Flask(__name__)

# Routing
@app.route('/', methods=['GET'])
def homepage():
    ytmusic = YTMusic()
    home_data = ytmusic.get_home(10)
    artists = []

    default_songs = []

    for data in home_data:
        if data['title'] == 'Quick picks':
            default_songs = data['contents']

    print(default_songs)
    return render_template('index.html', default_songs=default_songs)

@app.route('/search', methods=['GET'])
def search():
    ytmusic = YTMusic()
    search = request.args.get("search")
    search_results = ytmusic.search(search, filter="songs", limit=10)
    default_songs = []

    for song in search_results:
        default_songs.append(song)



    print(default_songs)
    return render_template('index.html', default_songs=default_songs, search=search)

