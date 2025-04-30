from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['smart-db']
collection = db['posts']

posts = collection.find()

for post in posts:
    print(post)
