from pymongo.mongo_client import MongoClient

#uri = "mongodb+srv://musicapp:u9rUOxxFyFcixBce@billscluster.rgqlbo3.mongodb.net/?retryWrites=true&w=majority&appName=BillsCluster"
uri = "mongodb://musicapp:u9rUOxxFyFcixBce@ac-qtjkjhm-shard-00-00.rgqlbo3.mongodb.net:27017,ac-qtjkjhm-shard-00-01.rgqlbo3.mongodb.net:27017,ac-qtjkjhm-shard-00-02.rgqlbo3.mongodb.net:27017/?ssl=true&replicaSet=atlas-weophv-shard-0&authSource=admin&retryWrites=true&w=majority&appName=BillsCluster"

print("Uri thing")

# Create a new client and connect to the server
client = MongoClient(uri)

print("boutta ping")

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print("You Failed:")
    print(e)

db = client["MusicUsers"]
col = db["UserName"]

one = col.find_one()
full = col.find()

for x in full:
  print(x)

print("")
print(one)