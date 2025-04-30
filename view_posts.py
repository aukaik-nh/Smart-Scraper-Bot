from pymongo import MongoClient

# เชื่อมต่อกับ MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['smart-db']
collection = db['posts']

# ดึงข้อมูลทั้งหมดจาก collection
posts = collection.find()

# แสดงข้อมูลทั้งหมด
for post in posts:
    print(post)
