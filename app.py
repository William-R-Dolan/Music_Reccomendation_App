from flask import Flask, render_template, request, redirect, url_for
from ytmusicapi import YTMusic
from pymongo.mongo_client import MongoClient
from bson import ObjectId

from urllib.request import urlopen

app = Flask(__name__)

uri = "mongodb://musicapp:u9rUOxxFyFcixBce@ac-qtjkjhm-shard-00-00.rgqlbo3.mongodb.net:27017,ac-qtjkjhm-shard-00-01.rgqlbo3.mongodb.net:27017,ac-qtjkjhm-shard-00-02.rgqlbo3.mongodb.net:27017/?ssl=true&replicaSet=atlas-weophv-shard-0&authSource=admin&retryWrites=true&w=majority&appName=BillsCluster"
# Create a new client and connect to the server
client = MongoClient(uri)


# Send a ping to confirm a successful connection
#try:
#    client.admin.command('ping')
#    print("Pinged your deployment. You successfully connected to MongoDB!")
#except Exception as e:
#    print(e)

#Connect to database

db = client["MusicUsers"]
user_col = db["UserName"]
#fav_col = db["Favourites"]
#playlist_col = db["Playlists"]
#Select the first user
current_user = user_col.find_one()
#Select the full list of users
user_full = user_col.find()
users = []

for x in user_full:
  users.append(x)
  #print(x)

print("")
print("Users:")
print(users)







# Routing
@app.route('/', methods=['GET'])
def homepage():
    global current_user
    global users
    ytmusic = YTMusic()
    home_data = ytmusic.get_home(10)
    artists = []

    default_songs = []

    for data in home_data:
        if data['title'] == 'Quick picks':
            default_songs = data['contents']


    #print("Favourites:")
    #print(favs)


    return render_template('index.html', default_songs=default_songs, users=users, username=current_user["name"], favourites=getFavourites())

@app.route('/search', methods=['GET'])
def search():
    global current_user
    global users
    ytmusic = YTMusic()
    search = request.args.get("search")
    search_results = ytmusic.search(search, filter="songs", limit=10)
    default_songs = []

    for song in search_results:
        default_songs.append(song)

    print(default_songs[1])
    return render_template('index.html', default_songs=default_songs, search=search, users=users, username=current_user["name"], favourites=getFavourites())

@app.route("/favourites", methods=['GET'])
def favourites():
    global current_user
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

        return render_template('index.html', default_songs=default_songs, users=users, username=current_user["name"], favourites=favs)
    else:
        return redirect(url_for('homepage'))

@app.route("/recommendations", methods=['GET'])
def recommendations():
    global current_user
    global users
    ytmusic = YTMusic()
    favs = getFavourites()
    if 'favs' in locals():
        default_songs = []
        print("a")
        related = ytmusic.get_watch_playlist(favs[0], limit=20)
        #print("tracks:")
        #print(related["tracks"][0])
        for song in related["tracks"]:
            song["thumbnails"] = song["thumbnail"]
            #print(song["thumbnail"])
            default_songs.append(song)
        print("Related:")
        print(related)

        return render_template('index.html', default_songs=default_songs, users=users, username=current_user["name"], favourites=favs)
    else:
        return redirect(url_for('homepage'))
@app.route('/changeuser', methods=['GET'])
def changeuser():
    global current_user
    global user_col
    new_user = request.args.get("newuser")
    new_user = user_col.find_one({"_id": ObjectId(new_user)})
    #print("New User:")
    #print(new_user)
    #print("Old User:")
    #print(current_user)
    current_user = new_user
    #print("Updated User:")
    #print(current_user)
    return redirect(url_for('homepage'))


@app.route('/addfavourite')
def addfavourite():
    global current_user
    global client
    db = client["MusicUsers"]
    fav_col = db["Favourites"]
    video_id = request.args.get("videoid")
    #print(video_id)

    data = {"user_id": current_user["_id"], "videoId": video_id}
    #print(data)
    fav_col.insert_one(data)
    return ("")

@app.route('/removefavourite')
def removefavourite():
    global current_user
    global client
    db = client["MusicUsers"]
    fav_col = db["Favourites"]
    video_id = request.args.get("videoid")
    data = {"user_id": current_user["_id"], "videoId": video_id}

    fav_col.delete_one(data)
    return ("")


def getFavourites():
    global current_user
    global client
    #Gets the user's favourites
    db = client["MusicUsers"]
    fav_col = db["Favourites"]
    fav_query = { "user_id": current_user["_id"]}
    favs_full = fav_col.find(fav_query)
    favs = [d['videoId'] for d in favs_full]
    return favs