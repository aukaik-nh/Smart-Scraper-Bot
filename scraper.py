from pymongo import MongoClient
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from datetime import datetime, timezone
import os
import time

def get_all_comments_from_popup(driver):
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[@role="dialog"]')))
        dialog = driver.find_element(By.XPATH, '//div[@role="dialog"]')

        while True:
            try:
                more_comments = dialog.find_element(
                    By.XPATH,
                    './/span[contains(text(),"ดูความคิดเห็นเพิ่มเติม") or contains(text(),"See more comments")]'
                )
                driver.execute_script("arguments[0].click();", more_comments)
                time.sleep(1.5)
            except:
                break

        while True:
            try:
                more_replies = dialog.find_element(
                    By.XPATH,
                    './/span[contains(text(),"ดูการตอบกลับ") or contains(text(),"View more replies")]'
                )
                driver.execute_script("arguments[0].click();", more_replies)
                time.sleep(1.5)
            except:
                break

        comment_blocks = dialog.find_elements(
            By.XPATH,
            './/div[contains(@class, "x1gslohp")]//div[@role="article"]/div[2]'
        )

        comments = []
        for block in comment_blocks:
            try:
                commenter_el = block.find_element(By.XPATH, './/a[@role="link"]//span/span')
                commenter_name = commenter_el.text.strip()

                text_elements = block.find_elements(
                    By.XPATH, './/div[@dir="auto" and string-length(normalize-space(text())) > 0]'
                )
                comment_text = " ".join(e.text.strip() for e in text_elements if e.text.strip())

                if commenter_name and comment_text:
                    comments.append({
                        "user": commenter_name,
                        "text": comment_text
                    })
                    print(f"{commenter_name}: {comment_text}")
            except:
                continue

        return comments
    except Exception as e:
        print(f"ไม่สามารถดึงคอมเมนต์: {e}")
        return []


def read_facebook_posts_and_store():
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

        page_url = 'https://www.facebook.com/jarpichit'
        driver.get(page_url)
        time.sleep(5)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[@role="article"]')))
        posts = driver.find_elements(By.XPATH, '//div[@role="article"]')
        posts = posts[:3]

        for idx, post in enumerate(posts):
            try:
                post_id_str = f'post_{idx}_{int(time.time())}'

                driver.execute_script("arguments[0].scrollIntoView(true);", post)
                time.sleep(2)

                try:
                    see_more = WebDriverWait(post, 2).until(
                        EC.element_to_be_clickable((By.XPATH, './/div[contains(text(),"ดูเพิ่มเติม") or contains(text(),"See More")]'))
                    )
                    driver.execute_script("arguments[0].click();", see_more)
                    time.sleep(1)
                except:
                    pass

                try:
                    link = post.find_element(By.XPATH, './/a[contains(@href, "/posts/")]')
                    driver.execute_script("arguments[0].click();", link)
                    time.sleep(3)
                except Exception as e:
                    print(f"ไม่สามารถเปิดโพสต์ {idx} แบบ popup: {e}")
                    continue

                try:
                    username_el = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, '//div[@role="dialog"]//h2//span//a | //div[@role="dialog"]//h3//span//a'))
                    )
                    username = username_el.text
                except:
                    username = "Unknown"

                try:
                    content_el = driver.find_element(By.XPATH, '//div[@role="dialog"]//div[@data-ad-preview="message"]//span')
                    post_content = content_el.text
                except:
                    post_content = ""

                image_urls = []
                try:
                    img_elements = post.find_elements(By.XPATH, './/img[contains(@src, "scontent")]')
                    for img in img_elements:
                        src = img.get_attribute('src')
                        if src and src not in image_urls:
                            image_urls.append(src)
                except:
                    pass

                print(f"โพสต์ {idx} โดย {username}: {post_content}")
                if image_urls:
                    print(f" {len(image_urls)} รูป")

                comments = get_all_comments_from_popup(driver)

                try:
                    close_btn = driver.find_element(By.XPATH, '//div[@aria-label="ปิด"] | //div[@aria-label="Close"]')
                    driver.execute_script("arguments[0].click();", close_btn)
                    time.sleep(2)
                except:
                    print("ไม่สามารถปิด popup ได้")

                if post_content.strip() or comments:
                    collection.insert_one({
                        'post_id': post_id_str,
                        'content': post_content,
                        'images': image_urls,
                        'username': username,
                        'comments': comments,
                        'timestamp': datetime.now(timezone.utc).isoformat() + 'Z'
                    })
                    print(f"บันทึกโพสต์ {idx} สำเร็จ")
                else:
                    print(f"โพสต์ที่ {idx} ไม่มีข้อมูลให้บันทึก")

            except Exception as e:
                print(f"เกิดข้อผิดพลาดในโพสต์ {idx}: {e}")

    finally:
        driver.quit()

if __name__ == "__main__":
    read_facebook_posts_and_store()
