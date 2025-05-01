import time
from scraper import crawl_facebook_post

def main_loop():
    while True:
        print("\n\n========== Start ==========")
        try:
            crawl_facebook_post()
            print("Completed")
        except Exception as e:
            print(f"Error: {e}")
        print("Break 6 hours\n")
        time.sleep(6 * 60 * 60)  # 6 hours
        # time.sleep(60)  # 1 minute

if __name__ == "__main__":
    main_loop()
