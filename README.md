# Smart-Scraper-Bot

1. ติดตั้ง MongoDB 
    - ดาวน์โหลด MongoDB (https://www.mongodb.com/try/download/community)
    - รัน : `mongodb://localhost:27017/`

2. pip install -r requirements.txt

3. cp .env.example .env

4. ใส่ข้อมูลลงในไฟล์ .env 
    - Login FB
    - MongoDB
    - FB TARGET URL

5. python scraper.py   

6. python cronjob.py -> call ทุกๆ 6 ชม.

