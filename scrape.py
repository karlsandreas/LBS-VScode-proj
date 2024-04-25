import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urljoin, urlparse
import time
import json
import os
import humanfriendly
import sys


def scroll_to_bottom(driver):
    # Scroll down to the bottom of the page
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    # Wait for a short time to let the content load
    time.sleep(2)

def extract_extensions(content):
    extensions = []

    soup = BeautifulSoup(content, 'lxml')
    
    extensions_source = soup.find_all('a', class_="gallery-item-card-container")
    
    for e in extensions_source:
        extension_properties = {}
        link  = urljoin(url ,e.get('href'))
        name = e.find(class_="item-title")

        downloads = e.find(class_="install-count")
        
        extension_properties["name"] = name.string
        extension_properties["link"] = link
        if downloads == None:
            extension_properties["downloads"] = 0
        else:
            extension_properties["downloads"] = humanfriendly.parse_size(downloads.string)

        #download_path = download_extension(link)
        extension_properties["path"] = ""

        extensions.append(extension_properties)
        #print(name.string + " " + link)
    
    return extensions 

def crawl_extensions(url):
    
    
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    time.sleep(3)

    for i in range(20):
        try:
            with open('extensions.json', 'r') as json_file:
                try:
                    exisiting_extensions = json.load(json_file)
                except:
                    exisiting_extensions = []
        except FileNotFoundError:
            print("File not found")
            quit(FileNotFoundError)

        exisiting_extensions_name = [data["name"] for data in exisiting_extensions] 

        content = driver.page_source
        new_extensions = extract_extensions(content)

        count = 0
        for n_e in new_extensions:
            if n_e["name"] not in exisiting_extensions_name:
                exisiting_extensions.append(n_e)
                count += 1
        

        scroll_to_bottom(driver)
        
        if count == 0:
            print("Nothing added, continue")
            continue

        with open('extensions.json', 'w') as json_file:
                json.dump(exisiting_extensions, json_file, indent=4)
                print(count,"Extensions added to",json_file.name)

    driver.quit()

def add_path(batch_size: int):
    try:
        with open('extensions.json', 'r') as json_file:
            try:
                exisiting_extensions = json.load(json_file)
            except:
                exisiting_extensions = []
    except FileNotFoundError:
            print("File not found")
            quit(FileNotFoundError)

    for extension in exisiting_extensions:
        count = 0
        if extension["path"] == "":
            print("Downloading extension", extension["name"])
            path = download_extension(extension["link"])
            if path != None:
                extension["path"] = path
                count += 1
            else:
                print("Failed to download", extension["name"])
        if count == 0:
            print("Nothing added, continue")
            continue

        #Save
        with open('extensions.json', 'w') as json_file:
            json.dump(exisiting_extensions, json_file, indent=4)
            print(count,"Extensions downloaded to",json_file.name)


def download_extension(url):
    
    download_dir = os.getcwd() + "/extensions_download/"
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_experimental_option("prefs",  {"download.default_directory": download_dir})
    driver = webdriver.Chrome(options=chrome_options)
    

    driver.get(url)

    time.sleep(2)

    download_button = driver.find_element(By.CSS_SELECTOR,'[aria-label="Download Extension"]')

    download_button.click()

    time.sleep(5)

    files = os.listdir(download_dir)
    
    # Filter out directories
    files = [file for file in files if os.path.isfile(os.path.join(download_dir, file))]
    
    # Sort files by modification time (mtime) in descending order
    files.sort(key=lambda x: os.path.getmtime(os.path.join(download_dir, x)), reverse=True)

    if files:
        latest_file = files[0]
        return os.path.relpath(os.path.join(download_dir, latest_file))
    else:
        return None


def main():
    args = sys.argv[1:] 
    url = urlparse(args[1])

    if args[0] == "scrape":
        if url.scheme and url.netloc:
            crawl_extensions(url)
        else:
            print("Invalid url", url)
    if args[0] == "add_path":
        if (int(args[1]) >= 1 and int(args[1]) <= 100):
            add_path(int(args[1]))

if __name__ == "__main__":
    main()