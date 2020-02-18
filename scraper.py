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

def get_longest_page_URL():
    return longestPageURL

def get_longest_page_word_count():
    return longestPageWordCount

def scraper(url, resp):
    links = extract_next_links(url, resp)
    validlinks = [link for link in links if is_valid(link)]
    return validlinks

def extract_next_links(url, resp):
    # If the raw_response exists, and the status is within 200 to 599, and is not 404 or 403,
    # then process the raw_response.content
    if resp:
        if not resp.raw_response == None:
            if resp.status >= 200 and resp.status <= 599:
                if resp.status == 404 or resp.status == 403:
                    return list()
                try:
                    # Get the HTML content and make it into a tree with lxml
                    parser = lxml.etree.HTMLParser(encoding='UTF-8')
                    tree = lxml.etree.parse(io.StringIO(resp.raw_response.content.decode(encoding='UTF-8')),parser)

                    # String of all the text on the page
                    pageTextString = ""

                    # Check these tags for text
                    wantedTags = {"p","span","blockquote","code","br","a","ol","ins","sub","sup","h1","h2","h3","h4","h5","h6","li","ul","title","b","strong","em","i","small","sub","sup","ins","del","mark","pre"}

                    parsed = urlparse(url)
                    
                    listofLinks = []
                    for elem in tree.iter():

                        if elem.tag in wantedTags:
                            if elem.text:
                                pageTextString += elem.text + " "

                        if elem.tag == "a" and "href" in elem.attrib: 
                            link = elem.attrib["href"]
                            if len(link) == 0:
                                continue
                            if link == r"/" or link == parsed.netloc:
                                continue
                            elif link[0] == r"/":
                                link = parsed.netloc + link
                            elif link[0:2] == r"//":
                                link = "https:" + link

                            link = link.split('#')[0]
                            if "replytocom=" in link or "share=" in link:
                                link = link.split('?')[0]
                            listofLinks.append(link)

                    # If the distance between this page's hash and any other page
                    # is less than 3, return an empty list because this page is
                    # too similar to another page to be useful
                    pageHash = Simhash(pageTextString)
                    minDist = 100000000000
                    for hashedPage in hashes:
                        if pageHash.distance(hashedPage) < minDist:
                            minDist = pageHash.distance(hashedPage)
                        if pageHash.distance(hashedPage) <= 3:
                            return list()
                    hashes.add(pageHash)
                    print(minDist)

                    # Tokenize the page and put the resulting list in pageListofWords
                    pageListofWords = []
                    currWord = ""
                    for char in pageTextString:
                        try:
                            charOrd = ord(char)
                            if (charOrd >= 64 and charOrd <= 90):
                                currWord += char.lower()
                            elif (charOrd >= 48 and charOrd <= 57) or (charOrd >= 97 and charOrd <= 122):
                                currWord += char
                            else:
                                if currWord != "":
                                    if not currWord in stopWords and len(currWord) > 1:
                                        pageListofWords.append(currWord)
                                    currWord = ""
                        except:
                            continue

                    # If the number of words is less than 150, return an empty list
                    # because this page is not useful enough
                    pageWordCount = len(pageListofWords)
                    if pageWordCount < 150:
                        return list()  

                    # If this page has more words than the current longest page,
                    # set this page as the new longest page
                    global longestPageWordCount
                    global longestPageURL
                    if pageWordCount > longestPageWordCount:
                        longestPageWordCount = pageWordCount
                        longestPageURL = url
                        print("New longest page: " + url + " " + str(longestPageWordCount))

                    # Increase word counters by their occurrences on this page
                    for word in pageListofWords:
                        if word not in stopWords:
                            if word not in totalWordDict:
                                totalWordDict[word] = 1
                            else:
                                totalWordDict[word] += 1

                    return listofLinks

                # Prints an exception if the page has non-UTF-8 characters
                except Exception as e:
                    print(e)

    # There was no response, or no content, or a bad resp_status
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

        # If this page is not in one of the validURLs, return false
        for baseURL in validURLs:
            if baseURL in parsed.netloc:
                flag = True
        if not flag:
            return False

        # Read the robots.txt for this url
        # Return false if we're not allowed to crawl this url
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