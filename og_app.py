from flask import Flask, render_template
from ytmusicapi import YTMusic

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

yt = YTMusic('oauth.json')
playlistId = yt.create_playlist('test', 'test description')
search_results = yt.search('Oasis Wonderwall')

print(search_results)