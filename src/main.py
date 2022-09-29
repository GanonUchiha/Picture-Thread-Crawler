
import asyncio
import argparse
import requests
import time
import traceback
from bs4 import BeautifulSoup
from pathlib import Path
import urllib.request

from requests.models import HTTPError


def parse_url(url):

    args = url.split("?")[-1].split("&")
    url = url.split("?")[0]
    board_id = -1
    thread_id = -1

    for arg in args:
        if arg.startswith("bsn="):
            board_id = int(arg.replace("bsn=", ""))
        elif arg.startswith("snA="):
            thread_id = int(arg.replace("snA=", ""))
    
    return url, board_id, thread_id

def get_webpage(url):
    
    HEADERS = {"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36"}

    response = requests.get(url, headers=HEADERS)
    retries = 3
    while response.status_code != 200 and retries > 0:
        time.sleep(1)
        response = requests.get(url, headers=HEADERS)
        retries -= 1

    if retries == 0:
        raise Exception("Page not found or deleted: {}".format(url))

    time.sleep(0.1)
    return response.text

class BahamutThread(BeautifulSoup):

    def __init__(self, webpage_text, webpage_url, get_webpage):
        super().__init__(webpage_text, features="lxml")
        self.get_webpage = get_webpage
        self.webpage_url = webpage_url
        self.get_total_pages()
        self.get_title()
    
    def get_total_pages(self):
        page_index = self.find(class_="BH-pagebtnA")
        self.pages = int(page_index.find_all("a")[-1].text)
    
    def get_page_by_number(self, page_num):
        page_url = self.webpage_url + "&page={}".format(page_num)
        webpage_text = self.get_webpage(page_url)
        return BahamutThread(webpage_text, page_url, self.get_webpage)
    
    def save_webpage(self, path):
        if path is not Path:
            try:
                path = Path(path).open("w")
            except:
                raise Exception("Please give a valid pathname or Path object")
        
        path.write(str(self))
    
    def get_posts(self):
        post_tags = self.find_all(class_="c-post")
        return [BahamutPost(str(tag)) for tag in post_tags]
    
    def get_title(self):
        self.title = self.find(class_=["c-post__header__title", "is-except"]).text

class BahamutPost(BeautifulSoup):

    def __init__(self, post_text):
        super().__init__(post_text, features="lxml")
        self.get_gpbp()
    
    def get_gpbp(self):
        gp = self.find(class_="gp").find("a").text
        if gp == "爆":
            self.gp = 1000
        else:
            self.gp = int(gp)

        bp = self.find(class_="bp").find("a").text
        if bp == "X":
            self.bp = 1000
        elif bp == "-":
            self.bp = 0
        else:
            self.bp = int(bp)
    
    def get_image_urls(self):
        self.image_urls = []
        article_content = self.find(class_="c-article__content")
        for image_tag in article_content.find_all(class_="photoswipe-image"):
            # print(image_tag)
            image_url = image_tag["href"]
            self.image_urls.append(image_url)

def crawl_images_from_webpage(thread_page: BahamutThread, path: Path, min_gp=5, max_bp=0):
    posts = thread_page.get_posts()

    for post in posts:
        if post.gp >= min_gp and post.bp <= max_bp:
            post.get_image_urls()
            for image_url in post.image_urls:
                image_name = image_url.split("/")[-1].lower()
                image_path = path.joinpath(image_name)
                try:
                    urllib.request.urlretrieve(image_url, image_path)
                except:
                    print(image_url)

async def crawl_thread(thread_url):
    output_path = "/mnt/d/james_v/Pictures/飛起來/巴哈"

    main_url, board_id, thread_id = parse_url(thread_url)
    webpage_url = "{}?bsn={}&snA={}".format(main_url, board_id, thread_id)
    print(webpage_url)
    try:
        first_page_text = get_webpage(webpage_url)
    except:
        return
    
    main_thread = BahamutThread(first_page_text, webpage_url, get_webpage)
    with Path(output_path).joinpath(main_thread.title) as path:
        path.mkdir(parents=True, exist_ok=True)
        checkpoint_path = path.joinpath("__counter.txt")
        if checkpoint_path.exists():
            checkpoint = int(checkpoint_path.read_text())
        else:
            checkpoint = 0

        for page in range(checkpoint, main_thread.pages):
            print(page)
            thread_page = main_thread.get_page_by_number(page)
            crawl_images_from_webpage(thread_page, path)
            checkpoint_path.write_text(str(page))

def parse_arguments():
    
    parser = argparse.ArgumentParser()
    # parser.add_argument("url", help="巴哈討論串網址")
    parser.add_argument("-l", "--list", action="store_true", help="讀取一文件中的網址清單")
    args = parser.parse_args()
    print(args)
    return args

def main():
    args = parse_arguments()

    if args.list:
        input_ = input("輸入文件檔名：")
        with open(input_) as fp:
            urls = fp.read().split("\n")
    else:
        input_ = input("輸入討論串網址：")
        urls = [input_]

    for url in urls:
        url, board_id, thread_id = parse_url(url)
        webpage_url = "{}?bsn={}&snA={}".format(url, board_id, thread_id)
        try:
            asyncio.run(crawl_thread(webpage_url))
        except Exception:
            print(webpage_url)
            traceback.print_exc()


if __name__ == "__main__":
    main()