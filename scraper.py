import re
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import lxml.etree
import io

"""
*.ics.uci.edu/*
*.cs.uci.edu/*
*.informatics.uci.edu/*
*stat.uci.edu/*

TODO:
- Analyze text, tokenize and record top 50 words?
- robots.txt politeness
- number of unique pages
- 
--- find a way to record this?
"""
rp = RobotFileParser()
robotFiles = dict()

def scraper(url, resp):
    links = extract_next_links(url, resp)
    validlinks = [link for link in links if is_valid(link)]
    # for link in validlinks:
    #     print(link)
    return validlinks

def extract_next_links(url, resp):
    listoflinks = []
    if resp:
        if not resp.raw_response == None:
            if resp.status >= 200 and resp.status <= 399: #or resp.status >= 500 and resp.status <= 599:
                try:
                    parser = lxml.etree.HTMLParser(encoding='UTF-8')
                    tree = lxml.etree.parse(io.StringIO(resp.raw_response.content.decode(encoding='UTF-8')),parser)

                    for elem in tree.iter():
                        if elem.tag == "a" and "href" in elem.attrib: 
                            link = elem.attrib["href"]
                            if link[0:4] == r"http":
                                listoflinks.append(link)
                            if link[0:2] == r"//":
                                listoflinks.append("https:" + link)
                            elif link[0] == r"/":
                                parsed = urlparse(url)
                                listoflinks.append(parsed.netloc + link)
                except:
                    pass
    return listoflinks

def is_valid(url):
    try:
        url = url.split('#')[0]
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        if re.match(r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False
        validURLs = ["ics.uci.edu","cs.uci.edu","informatics.uci.edu","stat.uci.edu","today.uci.edu/department/information_computer_sciences"]

        flag = False

        for i in validURLs:
            if i in parsed.netloc:
                flag = True
        if not flag:
            return False

        try:
            if parsed.netloc in robotFiles:
                if not robotFiles[parsed.netloc].can_fetch("*", url):
                    return False
            else:
                rp = RobotFileParser()
                rp.set_url(r"https://"+parsed.netloc+r"/robots.txt")
                rp.read() 
                robotFiles[parsed.netloc] = rp
                if not rp.can_fetch("*",url):
                    return False
        except:
            pass
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise