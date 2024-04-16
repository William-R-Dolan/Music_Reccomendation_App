from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from ytmusicapi import YTMusic
from pymongo.mongo_client import MongoClient
from bson import ObjectId
from collections import Counter

from urllib.request import urlopen
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

#Comment out for production:
# import keras
# from keras.preprocessing.sequence import pad_sequences
# import pickle
# import numpy as np
# import re


app = Flask(__name__)

#Sets up the session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#Creates a new client and connects to the database server
uri = "mongodb://musicapp:u9rUOxxFyFcixBce@ac-qtjkjhm-shard-00-00.rgqlbo3.mongodb.net:27017,ac-qtjkjhm-shard-00-01.rgqlbo3.mongodb.net:27017,ac-qtjkjhm-shard-00-02.rgqlbo3.mongodb.net:27017/?ssl=true&replicaSet=atlas-weophv-shard-0&authSource=admin&retryWrites=true&w=majority&appName=BillsCluster"
client = MongoClient(uri)

#Selects to the specific database and tables
db = client["MusicUsers"]
user_col = db["UserName"]
#Gets all user information and saves it in a list. Obviously this is incredibly insecure, but I'm just making the login a dropdown
user_full = user_col.find()
users = []
for x in user_full:
  users.append(x)




# Routes to the home page
@app.route('/', methods=['GET'])
def homepage():

    #If a user hasn't been set yet, redirect to the login page
    if not session.get("user"):
        return redirect("/login")

    #Gets the user from the session
    current_user = session.get("user")
    #Prepares the user data and youtube api
    global users
    ytmusic = YTMusic()
    #The videos displayed by default
    home_data = ytmusic.get_home(10)
    default_songs = []
    #Seperates the actual songs from everything else
    for data in home_data:
        if data['title'] == 'Quick picks':
            default_songs = data['contents']
    #Renders the home page
    return render_template('index.html', default_songs=default_songs, type="none", users=users, username=current_user["name"], favourites=getFavourites())

# Routes to the login page
@app.route("/login", methods=["POST", "GET"])
def login():
  # if form is submited
    if request.method == "POST":
        # Gets the updated user from the form
        new_user = user_col.find_one({"_id": ObjectId(request.form.get("user_id"))})
        # Set the user in the session
        session["user"] = new_user
        global users
        # Updates the recommendations to match the new user and redirects to the main page
        updateRecs()
        return redirect("/")
    #If the user is linked here from elsewhere, display the basic dropdown
    return render_template("login.html", users=users)

# Routes to the search page
@app.route('/search', methods=['GET'])
def search():
    #Gets user information and api
    current_user = session.get("user")
    global users
    ytmusic = YTMusic()
    #Gets the information from the search bar
    search = request.args.get("search")
    #Returns to home if the search is empty
    if search == "":
        return redirect("/")
    #Searches with the API
    search_results = ytmusic.search(search, filter="songs", limit=10)
    #Builds the list of songs to display
    default_songs = []
    for song in search_results:
        default_songs.append(song)

    # Renders the page
    return render_template('index.html', default_songs=default_songs, type="none", search=search, users=users, username=current_user["name"], favourites=getFavourites())

#Routes to favourites page
@app.route("/favourites", methods=['GET'])
def favourites():
    #Gets user information and api
    current_user = session.get("user")
    global users
    ytmusic = YTMusic()
    #Gets user favourites
    favs = getFavourites()

    #If the user has favourites cycle through them and format them for display
    if 'favs' in locals():
        default_songs = []
        for song in favs:
            #Favourites are only saved in the database as Ids, so the data has to be retrieved through the API
            songFormat = ytmusic.get_song(song)['videoDetails']
            #The formatting is less than ideal for display, so the important thumbnail data is moved
            songFormat['thumbnails'] = songFormat["thumbnail"]['thumbnails']
            del songFormat["thumbnail"]
            default_songs.append(songFormat)

        #Renders the favourites page
        return render_template('index.html', default_songs=default_songs, type="favourites", users=users, username=current_user["name"], favourites=favs)
    else:
        #Redirect home if the user has no favourites
        return redirect(url_for('homepage'))

# Routes to the recommendations page
@app.route("/recommendations", methods=['GET'])
def recommendations():
    #Gets user information and api
    current_user = session.get("user")
    global users
    ytmusic = YTMusic()
    #Gets favourites for reference
    favs = getFavourites()
    #Only continues if the user actually has favourites
    if 'favs' in locals():
        default_songs = []
        #Recommendations are stored in the session to try and speed things up.
        #If they haven't been stored yet, then do that now.
        if not session.get("recs"):
            updateRecs()
        if not session.get("recs"):
            #If a list of recommendations can't be created for some reason return home.
            return redirect("/")
        #Gets recommendations from the session
        all_recs = session.get("recs")

        #Builds list out of top 20 related songs. Recs ARE ordered by relevance
        for rec in all_recs[:20]:
            #Gets the songs from the API and formats them for display
            song = ytmusic.get_song(rec)['videoDetails']
            song["thumbnails"] = song["thumbnail"]['thumbnails']
            default_songs.append(song)

        #Renders the Recommendations page
        return render_template('index.html', default_songs=default_songs, type="recommendations", users=users, username=current_user["name"], favourites=favs)
    else:
        #Returns home if the user does not have a favourites list for reference
        return redirect(url_for('homepage'))

#Routes to playlist generation
@app.route("/playlists", methods=['GET'])
def playlists():
    #Redirect code for production
    return redirect("/")

    #Gets user information and api
    current_user = session.get("user")
    global users
    ytmusic = YTMusic()
    favs = getFavourites()
    
    #Loads the model and tokenizer
    model = keras.saving.load_model("model.keras")
    tokenizer = pickle.load(open('tokenizer.pickle', 'rb'))

    #So long as the user has favourites, analyze their genre preferences.
    if 'favs' in locals():
        default_songs = []
        user_genres = []
        playlist_genre = ""

        #For each favourite, get the song data and find the lyrics using the api
        for favourite in favs:
            related = ytmusic.get_watch_playlist(favourite, limit=1)
            lyrics = ""
            #As long as there is an ID for lyrics, get lyrics
            if related["lyrics"] != None:
                lyrics = ytmusic.get_lyrics(related["lyrics"])
            #So long as the lyric import isn't empty:
            if lyrics["lyrics"] != None:
                #Removes capitalization, punctuation, and other special characters from the lyrics
                lyrics = [ scrubLyrics(lyrics) ]
                #Converts the lyrics into tokens
                sequence = tokenizer.texts_to_sequences(lyrics)
                #Pad the sequence so it can be read by the model
                input = pad_sequences(sequence, maxlen=25, dtype='int32', value=0)
                #Uses the model to predict the genre based on the lyrics
                genre = model.predict(input,batch_size=2,verbose = 0)[0]

                #This is unnecessary, I just like to see the genres it assigns to each song in the terminal
                song = ytmusic.get_song(favourite)['videoDetails']
                print("===============================")

                #Translates the genre back to text
                song_genre = np.argmax(genre)
                if (song_genre == 0):
                    print(song["title"] + ": Hip-Hop")
                    user_genres.append("Hip-Hop")
                elif (song_genre == 1):
                    print(song["title"] + ": Pop")
                    user_genres.append("Pop")
                elif (song_genre == 2):
                    print(song["title"] + ": Country")
                    user_genres.append("Country")
                elif (song_genre == 3):
                    print(song["title"] + ": Rock")
                    user_genres.append("Rock")
                elif (song_genre == 4):
                    print(song["title"] + ": RnB")
                    user_genres.append("Rhythm and Blues")
                elif (song_genre == 5):
                    print(song["title"] + ": Dance")
                    user_genres.append("Electronic and Dance")

        #Finds the top genres for the user
        user_genres = [item for items, c in Counter(user_genres).most_common()
                                      for item in [items] * c]
        ordered_genres = list(dict.fromkeys(user_genres))

        #If the user listens to more than one genre significantly, then search for playlists with one or both genres
        if (len(ordered_genres) != 1):
            if(user_genres.count(ordered_genres[0])*3 > user_genres.count(ordered_genres[1])*2):
                playlist_genre = ordered_genres[0]
            else:
                playlist_genre = ordered_genres[0] + " and " + ordered_genres[1]
        else:
            #Otherwise, just look for playlists containing the user's favourite genre
            playlist_genre = ordered_genres[0]
        #Formats the query and searches using the api
        playlist_genre += " music"
        search_results = ytmusic.search(playlist_genre, filter="playlists", limit=3)

        #Formats the search results for display
        for song in search_results:
            song["playlistId"] = song["browseId"][2:]
            default_songs.append(song)

        return render_template('index.html', default_songs=default_songs, type="playlists", users=users, username=current_user["name"], favourites=favs)
    else:
        #Redirects home if the user has no favourites
        return redirect(url_for('homepage'))

#Function for adding favourites
@app.route('/addfavourite')
def addfavourite():
    #Gets the user and Database info
    current_user = session.get("user")
    global client
    db = client["MusicUsers"]
    fav_col = db["Favourites"]
    video_id = request.args.get("videoid")
    #Formats the new link table entry
    data = {"user_id": current_user["_id"], "videoId": video_id}
    #Inserts the new entry into the database
    fav_col.insert_one(data)
    #Updates recommendations based on new favourite data
    updateRecs()
    return ("")

#Function for removing favourites
@app.route('/removefavourite')
def removefavourite():
    #Gets the user and Database info
    current_user = session.get("user")
    global client
    db = client["MusicUsers"]
    fav_col = db["Favourites"]
    video_id = request.args.get("videoid")
    #Formats the deletion query
    data = {"user_id": current_user["_id"], "videoId": video_id}
    #Deletes the database entry
    fav_col.delete_one(data)
    #Updates recommendations based on new favourite data
    updateRecs()
    return ("")

#Updates user recommendations
def updateRecs():
    #Prepares fields, favourites and the api
    all_recs = []
    favs = getFavourites()
    ytmusic = YTMusic()

    #Finds songs related to favourites
    for fav_song in favs:
        related = ytmusic.get_watch_playlist(fav_song, limit=8)
        for song in related["tracks"]:
            all_recs.append(song["videoId"])
    #Prioritizes songs recommended multiple times
    all_recs = [item for items, c in Counter(all_recs).most_common()
                                      for item in [items] * c]
    #removes duplicates
    all_recs = list(dict.fromkeys(all_recs))
    #Debug notification
    print("Updated Recommendations!")
    #Saves updated recommendations to the session
    session["recs"] = all_recs

#Function for retrieving user favourites
def getFavourites():
    #Gets current user
    current_user = session.get("user")
    global client
    #Connects to the database
    db = client["MusicUsers"]
    fav_col = db["Favourites"]
    #Querys the link table, getting all song IDs linked to the current user id
    fav_query = { "user_id": current_user["_id"]}
    favs_full = fav_col.find(fav_query)
    #Formats favourite ids.
    favs = [d['videoId'] for d in favs_full]
    return favs

#Removes capitals, punctuation, and special characters from lyrics
def scrubLyrics(lyrics):
    #An immidiate return function for production
    return ""
    lyrics = lyrics['lyrics']
    if lyrics != None:
        #Changes lyrics to lowercase
        lyrics = lyrics.lower()
        #I believe these first two are unneccissary and handled by the third one, but I'll keep them there just in case
        lyrics = re.sub(r'\\n', ' ', lyrics)
        lyrics = re.sub(r'\\r', ' ', lyrics)
        lyrics = re.sub(r'[^a-z\s]+', ' ', lyrics)
    else:
        #There has to be lyrics to format in order to format the lyrics.
        print("Scammed")
        lyrics = ""
    return lyrics