from pymongo import MongoClient
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException
from datetime import datetime, timezone
import os
import time

def get_comments(driver):
    try:
        container = driver.find_element(By.XPATH, '//div[@role="dialog"]') if driver.find_elements(By.XPATH, '//div[@role="dialog"]') else driver.find_element(By.TAG_NAME, 'body')

        while True:
            try:
                more_comments = container.find_element(By.XPATH, './/span[contains(text(),"ดูความคิดเห็นเพิ่มเติม") or contains(text(),"See more comments")]')
                driver.execute_script("arguments[0].click();", more_comments)
                time.sleep(2)
            except:
                break

        while True:
            try:
                more_replies = container.find_element(By.XPATH, './/span[contains(text(),"ดูการตอบกลับ") or contains(text(),"View more replies")]')
                driver.execute_script("arguments[0].click();", more_replies)
                time.sleep(2)
            except:
                break

        time.sleep(5)

        comment_blocks = driver.find_elements(By.XPATH, '//div[contains(@class, "x1gslohp")]//div[@role="article"]/div[2]')
        comments = []

        for i in range(len(comment_blocks)):
            for _ in range(3):
                try:
                    block = comment_blocks[i]
                    commenter_name = block.find_element(By.XPATH, './/a[@role="link"]//span/span').text.strip()
                    text_elements = block.find_elements(By.XPATH, './/div[@dir="auto" and string-length(normalize-space(text())) > 0]')
                    comment_text = " ".join(e.text.strip() for e in text_elements if e.text.strip())

                    if commenter_name and comment_text:
                        comments.append({
                            "user": commenter_name,
                            "text": comment_text
                        })
                    break
                except StaleElementReferenceException:
                    time.sleep(1)
                    comment_blocks = driver.find_elements(By.XPATH, '//div[contains(@class, "x1gslohp")]//div[@role="article"]/div[2]')
                except:
                    break
        return comments
    except:
        return []

def crawl_facebook_post():
    load_dotenv()
    fb_email = os.getenv('FB_EMAIL')
    fb_password = os.getenv('FB_PASSWORD')
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')

    client = MongoClient(mongo_uri)
    db = client['smart-db']
    collection = db['posts']

    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-notifications')
    driver = webdriver.Chrome(options=options)

    try:
        driver.get('https://www.facebook.com/login')
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, 'email'))).send_keys(fb_email)
        driver.find_element(By.ID, 'pass').send_keys(fb_password)
        driver.find_element(By.ID, 'pass').send_keys(Keys.RETURN)
        time.sleep(5)

        driver.get('https://www.facebook.com/jarpichit')
        time.sleep(5)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[@role="article"]')))
        posts = driver.find_elements(By.XPATH, '//div[@role="article"]')[:3]

        saved_count = 0

        for idx in range(len(posts)):
            try:
                post_id_str = f'post_{idx}_{int(time.time())}'

                for _ in range(3):
                    try:
                        post = posts[idx]
                        driver.execute_script("arguments[0].scrollIntoView(true);", post)
                        time.sleep(2)

                        try:
                            see_more = post.find_element(By.XPATH, './/div[contains(text(),"ดูเพิ่มเติม") or contains(text(),"See More")]')
                            driver.execute_script("arguments[0].click();", see_more)
                            time.sleep(1)
                        except:
                            pass

                        try:
                            link = post.find_element(By.XPATH, './/a[contains(@href, "/posts/")]')
                            driver.execute_script("arguments[0].click();", link)
                            time.sleep(3)
                        except:
                            break
                        break
                    except StaleElementReferenceException:
                        time.sleep(1)
                        posts = driver.find_elements(By.XPATH, '//div[@role="article"]')

                try:
                    username = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, '//div[@role="dialog"]//h2//span//a | //div[@role="dialog"]//h3//span//a'))
                    ).text
                except:
                    username = ""

                try:
                    post_content = driver.find_element(By.XPATH, '//div[@role="dialog"]//div[@data-ad-preview="message"]//span').text
                except:
                    post_content = ""

                image_urls = []
                try:
                    img_elements = driver.find_elements(By.XPATH, '//div[@role="dialog"]//img[contains(@src, "scontent")]')
                    for img in img_elements:
                        src = img.get_attribute('src')
                        if src and src not in image_urls:
                            image_urls.append(src)
                except:
                    pass

                comments = get_comments(driver)

                try:
                    close_btn = driver.find_element(By.XPATH, '//div[@aria-label="ปิด"] | //div[@aria-label="Close"]')
                    driver.execute_script("arguments[0].click();", close_btn)
                    time.sleep(2)
                except:
                    pass

                if post_content.strip() or comments:
                    collection.insert_one({
                        'post_id': post_id_str,
                        'content': post_content,
                        'images': image_urls,
                        'username': username,
                        'comments': comments,
                        'timestamp': datetime.now(timezone.utc).isoformat() + 'Z'
                    })
                    saved_count += 1

            except:
                continue

        print(f"เก็บโพสต์สำเร็จจำนวน {saved_count} โพสต์")

    finally:
        driver.quit()

if __name__ == "__main__":
    crawl_facebook_post()
