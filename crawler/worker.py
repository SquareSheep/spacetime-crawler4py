from threading import Thread

from utils.download import download
from utils import get_logger
from scraper import *
import time

from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

# Stores the robot_parser objects for each base URL
robotFiles = dict()
# Number of unique pages for each subdomain
uniqueSubdomains = dict()
# Total number of unique URLs
numberofUniquePages = 4
#Total number of URL links
totalNumberofURLs = 4

class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        super().__init__(daemon=True)
        
    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break

            try:
                parsed = urlparse(tbd_url)
                if not parsed.netloc in robotFiles:
                    rp = RobotFileParser()
                    rp.set_url(r"https://"+parsed.netloc+r"/robots.txt")
                    rp.read()
                    robotFiles[parsed.netloc] = rp
                if not robotFiles[parsed.netloc].can_fetch("*", url):
                    continue
            except:
                pass

            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper(tbd_url, resp)

            global numberofUniquePages
            global totalNumberofURLs
            for scraped_url in scraped_urls:
                totalNumberofURLs += 1
                if self.frontier.add_url(scraped_url):
                    numberofUniquePages += 1
                    parsed = urlparse(scraped_url)
                    if "ics.uci.edu" in parsed.netloc:
                        if parsed.netloc not in uniqueSubdomains:
                            uniqueSubdomains[parsed.netloc] = 1
                            print(parsed.netloc + " " + str(uniqueSubdomains[parsed.netloc]))
                        else:
                            uniqueSubdomains[parsed.netloc] += 1
                            print(parsed.netloc + " " + str(uniqueSubdomains[parsed.netloc]))

            self.frontier.mark_url_complete(tbd_url)

            # If the robots.txt asks for a different delay, time.sleep by that much plus the normal 0.5 seconds
            if parsed.netloc in robotFiles and robotFiles[parsed.netloc].default_entry is not None:
                timeDelay = robotFiles[parsed.netloc].crawl_delay('*')
                if timeDelay is not None:
                    time.sleep(timeDelay)

            time.sleep(self.config.time_delay)

        # Once the crawler finishes, print the relevant stats
        print("Total number of URL links: " + str(totalNumberofURLs))
        print("Total number of unique URLs: " + str(numberofUniquePages))
        print("Longest page: " + get_longest_page_URL())
        print("with " + str(get_longest_page_word_count()) + " words")

        i = 0
        print("50 most common words: ")
        for word in sorted(totalWordDict,key = lambda x: -totalWordDict[x]):
            print(word + ": " + str(totalWordDict[word]))
            i += 1
            if i == 50:
                break

        print("Number of unique pages for each subdomain in ics.uci.edu: ")
        for domain in uniqueSubdomains:
            print(domain, uniqueSubdomains[domain])
