"""
Author: Ghost (official.ghost@tuta.io)
Readme:
    This is unofficial, and not related with Anime Heaven.
    It is written just for convinient, feel free to share or edit
    Animes are credited to AnimeHeaven.eu

https://github.com/hadesy2k/ahdownloader
"""


import urllib.request
import re
from collections import OrderedDict

from bs4 import BeautifulSoup
from progressbar import ProgressBar, Percentage, Bar, RotatingMarker, ETA, FileTransferSpeed
from selenium import webdriver

import time
from random import randint
from threading import Thread, Lock

class Downloader:
    def __init__(self, url, epRange):
        """ url -> string
            episode -> string (from-to) """
        self.driver = webdriver.PhantomJS()
        self.downloads = []  # sort episodes in asending order
        self.pbar = ""  # Download Progressbar
        self.list_lock = Lock()
        self.download_lock = Lock()
        self.fetch_complete = False
        self.Main(url, epRange)
        

    def Main(self, url, epRange):
        """ Main Method """

        # Create a separate thread for download jobs
        thread = Thread(target=self.workerDownload, name='Download', args=())
        thread.start()
        
        # Fetching urls in parallel to download jobs
        print("[-] Getting episodes urls")
        for episode_number in self.getRange(epRange):  # Episode Range
            fetch_success = False
            while not fetch_success:
                html = self.fetchUrl(url + "&e=" + str(episode_number))
                # When abuse protection is triggered, the html document does
                # not provide a link to any video. Therefore, we wait
                # for some time to repeat fetching the url
                abuse_message = 'You have triggered abuse protection'
                if html.find(abuse_message)==-1:
                    fetch_success = True
                else:
                    timeout = 2
                    # print('[-] You might have triggered abuse protection')
                    # print('[-] Fetching url postponed by {} minutes'.format(timeout))
                    time.sleep(timeout*60)
            if html != None:
                self.getDownload(html, episode_number)
            else:
                print("[404] url not found for episode " + str(episode_number))
        self.fetch_complete = True
        
        thread.join()
        print("\n[+] Finished downloading. Enjoy your anime.")

    def getRange(self, epRange):
        """ return list of numbers (range) from given str format (min-max) """
        epRange = list(map(int, epRange.split('-')))
        if len(epRange) > 1:
            return list(range(epRange[0], epRange[1]+1))
        else:
            return epRange

    def fetchUrl(self, url):
        """ return website source code """
        self.driver.get(url)
        html = self.driver.page_source
        return html

    def getDownload(self, html, episode_number):
        """ scrap the download link from the given HTML source """
        soup = BeautifulSoup(html, "html.parser")
        download = soup.find_all('source')
        if download:
            self.list_lock.acquire() # prevent simultaneous append and pop of list
            self.downloads.append(("Episode %s.mp4" % str(episode_number), download[0]['src']))
            self.list_lock.release()
            return

        print("[!] Download link not found for episode %s" % str(episode_number))

    def workerDownload(self):
        """ download next item in list in a seperate thread """
        print("[-] Downloading process started\n")
        while not self.fetch_complete or self.downloads:
            time.sleep(2)
            if self.downloads:
                self.list_lock.acquire() # prevent simultaneous append and pop of list
                filename, url = self.downloads.pop(0)
                self.list_lock.release()
                self.downloadFile(filename, url)

    def downloadFile(self, filename, url):
        """ download the video """
        self.setProgressBar(filename)
        # For mulitple parallel downloads uncomment locks
        self.download_lock.acquire() # allow only one download at a time
        urllib.request.urlretrieve(url, filename, reporthook=self.progressBar)
        self.download_lock.release()
        self.pbar.finish()

    def setProgressBar(self, filename):
        """ Reset Progressbar """
        self.pbar = ProgressBar(widgets=[filename.replace(".mp4", " "), Percentage(), ' ', Bar(marker=RotatingMarker()), ' ', ETA(), ' ', FileTransferSpeed()])

    def progressBar(self, count, blockSize, totalSize):
        if self.pbar.maxval is None:
            self.pbar.maxval = totalSize
            self.pbar.start()
        self.pbar.update(min(count*blockSize, totalSize))


def banner():
    print("Anime Heaven Downloader by Ghost (https://github.com/the-robot/animeheaven-downloader)")
    print("Check above url for how to use the script.\n")


if __name__ == "__main__":
    banner()

    try:
        anime = input("Enter Anime Url (with http): ")
        epRange = input("Enter episode no. or in range [from-to]: ")
        Downloader(anime, epRange)
    except KeyboardInterrupt:
        exit()
