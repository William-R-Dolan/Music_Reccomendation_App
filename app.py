from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from ytmusicapi import YTMusic
from pymongo.mongo_client import MongoClient
from bson import ObjectId
from collections import Counter

#import keras
#import pickle

from urllib.request import urlopen
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

Session(app)



uri = "mongodb://musicapp:u9rUOxxFyFcixBce@ac-qtjkjhm-shard-00-00.rgqlbo3.mongodb.net:27017,ac-qtjkjhm-shard-00-01.rgqlbo3.mongodb.net:27017,ac-qtjkjhm-shard-00-02.rgqlbo3.mongodb.net:27017/?ssl=true&replicaSet=atlas-weophv-shard-0&authSource=admin&retryWrites=true&w=majority&appName=BillsCluster"
# Create a new client and connect to the server
client = MongoClient(uri)


db = client["MusicUsers"]
user_col = db["UserName"]
user_full = user_col.find()
users = []

for x in user_full:
  users.append(x)

print("")
print("Users:")
print(users)







# Routing
@app.route('/', methods=['GET'])
def homepage():

    #model = keras.saving.load_model("model.keras")
    #tokenizer = pickle.load(open('tokenizer.pickle', 'rb'))



    if not session.get("user"):
        # if not there in the session then redirect to the login page
        return redirect("/login")

    current_user = session.get("user")
    global users
    ytmusic = YTMusic()
    home_data = ytmusic.get_home(10)
    artists = []
    print("User Name")
    print(current_user)
    default_songs = []

    for data in home_data:
        if data['title'] == 'Quick picks':
            default_songs = data['contents']


    #print("Favourites:")
    #print(favs)


    return render_template('index.html', default_songs=default_songs, type="none", users=users, username=current_user["name"], favourites=getFavourites())


@app.route("/login", methods=["POST", "GET"])
def login():
  # if form is submited
    if request.method == "POST":
        print(request.form.get("user_id"))
        new_user = user_col.find_one({"_id": ObjectId(request.form.get("user_id"))})
        print("User Name")
        print(new_user)
        # record the user name
        session["user"] = new_user
        global users
        # redirect to the main page
        print(session.get("user"))
        updateRecs()
        return redirect("/")
    return render_template("login.html", users=users)


@app.route('/search', methods=['GET'])
def search():
    current_user = session.get("user")
    global users
    ytmusic = YTMusic()
    search = request.args.get("search")
    search_results = ytmusic.search(search, filter="songs", limit=10)
    default_songs = []

    for song in search_results:
        default_songs.append(song)

    print(default_songs[1])
    return render_template('index.html', default_songs=default_songs, type="none", search=search, users=users, username=current_user["name"], favourites=getFavourites())

@app.route("/favourites", methods=['GET'])
def favourites():
    current_user = session.get("user")
    global users
    ytmusic = YTMusic()
    favs = getFavourites()
    if 'favs' in locals():
        default_songs = []

        for song in favs:
            print("Song")

            songFormat = ytmusic.get_song(song)['videoDetails']
            songFormat['thumbnails'] = songFormat["thumbnail"]['thumbnails']
            del songFormat["thumbnail"]
            print(songFormat)
            default_songs.append(songFormat)

        print("Default Songs:")
        #default_songs = default_songs[0]
        print(default_songs)

        return render_template('index.html', default_songs=default_songs, type="favourites", users=users, username=current_user["name"], favourites=favs)
    else:
        return redirect(url_for('homepage'))

@app.route("/recommendations", methods=['GET'])
def recommendations():
    current_user = session.get("user")
    global users
    ytmusic = YTMusic()
    favs = getFavourites()
    if 'favs' in locals():
        default_songs = []

        if not session.get("recs"):
            updateRecs()
        if not session.get("recs"):
            print("WHYYYYYYYYYYYYYYYYYYYYYYYY")
            return redirect("/")

        all_recs = session.get("recs")

        #Builds list out of top 20 related songs
        for rec in all_recs[:20]:
            song = ytmusic.get_song(rec)['videoDetails']
            song["thumbnails"] = song["thumbnail"]['thumbnails']
            default_songs.append(song)

        return render_template('index.html', default_songs=default_songs, type="recommendations", users=users, username=current_user["name"], favourites=favs)
    else:
        return redirect(url_for('homepage'))


@app.route('/addfavourite')
def addfavourite():
    current_user = session.get("user")
    global client
    db = client["MusicUsers"]
    fav_col = db["Favourites"]
    video_id = request.args.get("videoid")
    #print(video_id)

    data = {"user_id": current_user["_id"], "videoId": video_id}
    #print(data)
    fav_col.insert_one(data)
    updateRecs()
    return ("")

@app.route('/removefavourite')
def removefavourite():
    current_user = session.get("user")
    global client
    db = client["MusicUsers"]
    fav_col = db["Favourites"]
    video_id = request.args.get("videoid")
    data = {"user_id": current_user["_id"], "videoId": video_id}

    fav_col.delete_one(data)
    updateRecs()
    return ("")

def updateRecs():
    all_recs = []
    favs = getFavourites()
    ytmusic = YTMusic()

    for fav_song in favs:
        related = ytmusic.get_watch_playlist(fav_song, limit=20)
        for song in related["tracks"]:
            #song["thumbnails"] = song["thumbnail"]
            all_recs.append(song["videoId"])

    all_recs = [item for items, c in Counter(all_recs).most_common()
                                      for item in [items] * c]
    #print(all_recs)
    #removes duplicates
    all_recs = list(dict.fromkeys(all_recs))
    print("Updated Recommendations!")
    session["recs"] = all_recs

def getFavourites():
    current_user = session.get("user")
    global client
    #Gets the user's favourites
    db = client["MusicUsers"]
    fav_col = db["Favourites"]
    fav_query = { "user_id": current_user["_id"]}
    favs_full = fav_col.find(fav_query)
    favs = [d['videoId'] for d in favs_full]
    return favs