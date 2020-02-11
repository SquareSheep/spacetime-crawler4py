import re
from urllib.parse import urlparse
import lxml.etree
import io
from simhash import Simhash

"""
Tokenize words correctly
Print 1-4 answers at the end

"""

stopWords = {"a","about","above","after","again","against","all","am","an","and","any","are","aren't","as","at","be","because","been","before","being","below","between","both","but","by","can't","cannot","could","couldn't","did","didn't","do","does","doesn't","doing","don't","down","during","each","few","for","from","further","had","hadn't","has","hasn't","have","haven't","having","he","he'd","he'll","he's","her","here","here's","hers","herself","him","himself","his","how","how's","i","i'd","i'll","i'm","i've","if","in","into","is","isn't","it","it's","its","itself","let's","me","more","most","mustn't","my","myself","no","nor","not","of","off","on","once","only","or","other","ought","our","ours ourselves","out","over","own","same","shan't","she","she'd","she'll","she's","should","shouldn't","so","some","such","than","that","that's","the","their","theirs","them","themselves","then","there","there's","these","they","they'd","they'll","they're","they've","this","those","through","to","too","under","until","up","very","was","wasn't","we","we'd","we'll","we're","we've","were","weren't","what","what's","when","when's","where","where's","which","while","who","who's","whom","why","why's","with","won't","would","wouldn't","you","you'd","you'll","you're","you've","your","yours","yourself","yourselves"}

hashes = set()

longestPageURL = ""
longestPageWordCount = 0

totalWordDict = dict()

def scraper(url, resp):
    links = extract_next_links(url, resp)
    validlinks = [link for link in links if is_valid(link)]
    return validlinks

def extract_next_links(url, resp):
    if resp:
        if not resp.raw_response == None:
            if resp.status >= 200 and resp.status <= 599:
                if resp.status == 404:
                    return list()
                try:
                    parser = lxml.etree.HTMLParser(encoding='UTF-8')
                    tree = lxml.etree.parse(io.StringIO(resp.raw_response.content.decode(encoding='UTF-8')),parser)
                    listoflinks = []
                    currentPageWordCount = 0

                    pageText = ""

                    wantedTags = {"p","h1","h2","h3","h4","h5","h6","li","ul","title","b","strong","em","i","small","sub","sup","ins","del","mark","pre"}

                    for elem in tree.iter():
                        if elem.tag in wantedTags:
                            if elem.text:
                                currentPageWordCount += len(elem.text.split())
                                pageText += elem.text

                        if elem.tag == "a" and "href" in elem.attrib: 
                            link = elem.attrib["href"]

                            if link[0:2] == r"//":
                                link = "https:" + link
                            elif link[0] == r"/":
                                parsed = urlparse(url)
                                link = parsed.netloc + link

                            link = link.split('#')[0]
                            listoflinks.append(link)

                    print(currentPageWordCount)

                    pageHash = Simhash(pageText)

                    minDist = 100000000000

                    for hashedPage in hashes:
                        if pageHash.distance(hashedPage) < minDist:
                            minDist = pageHash.distance(hashedPage)
                        if pageHash.distance(hashedPage) < 3:
                            return list()
                    print(minDist)

                    hashes.add(pageHash)

                    if currentPageWordCount < 100:
                        return list()

                    global longestPageWordCount
                    global longestPageURL
                    if currentPageWordCount > longestPageWordCount:
                        longestPageWordCount = currentPageWordCount
                        longestPageURL = url
                        print("New longest URL: " + url + " " + str(longestPageWordCount))

                    currentPageListofWords = pageText.split()
                    for word in currentPageListofWords:
                        if word not in stopWords:
                            if word not in totalWordDict:
                                totalWordDict[word] = 1
                            else:
                                totalWordDict[word] += 1



                    return listoflinks

                except Exception as e:
                    print(e)
    return list()

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
        validURLs = [".ics.uci.edu",".cs.uci.edu",".informatics.uci.edu",".stat.uci.edu",".today.uci.edu/department/information_computer_sciences"]

        flag = False

        for i in validURLs:
            if i in url:
                flag = True
        if not flag:
            return False

        try:
            if not parsed.netloc in robotFiles:
                rp = RobotFileParser()
                rp.set_url(r"https://"+parsed.netloc+r"/robots.txt")
                rp.read()
                robotFiles[parsed.netloc] = rp
            if not robotFiles[parsed.netloc].can_fetch("*", url):
                return False
        except:
            pass
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise