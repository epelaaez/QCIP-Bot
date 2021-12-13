import twitter
import feedparser
import os
import urllib.request as libreq

# Initialize Twitter API
api = twitter.Api(consumer_key=os.environ["CONSUMER_KEY"],
                  consumer_secret=os.environ["CONSUMER_SECRET"],
                  access_token_key=os.environ["ACCESS_TOKEN"],
                  access_token_secret=os.environ["ACCESS_SECRET"])

# Get last Tweet
timeline   = api.GetUserTimeline(user_id=1469787460620193793, screen_name="quantcompinf", count=1)
last_tweet = None
if len(timeline) > 0:
    last_tweet = timeline[0].text

# Query the arXiv API
arxiv_query = "http://export.arxiv.org/api/query?search_query=cat:quant-ph+AND+%28"
terms       = [
                "gates",
                "compute",
                "computation", 
                "information", 
                "qubit", 
                "bit", 
                "algorithm", 
                "%22error+correct%22", 
                "cryptography", 
                "encryption", 
                "data", 
                "nisq", 
                "transpilation", 
                "processor", 
                "communication", 
                "anneal", 
                "code", 
                "circuit", 
                "%22machine+learning%22", 
                "%22neural+network%22", 
                "oracle"
            ]
for term in terms:
    arxiv_query += f"abs:{term}+OR+"
arxiv_query  = arxiv_query[:-4]
arxiv_query += "%29&sortBy=lastUpdatedDate&sortOrder=descending&max_results=1"

# Fetch data and concatenate
with libreq.urlopen(arxiv_query) as url:
    publications = url.read()
data  = feedparser.parse(publications)['entries'][0]
title = " ".join(data.title.split())
summ  = " ".join(data.summary.split())
link  = data.link
if len(data.authors) < 6:
    auth = ", ".join(author.name for author in data.authors)
else:
    auth  = ", ".join(data.authors[i].name for i in range(5))
    auth += " et al"
tweet = f"{link}\n\n\"{title}\" by {auth}.\n\nSummary: {summ}" 

if len(tweet) > 280:
    # Divide into multiple Tweets for thread
    tweets = []
    while len(tweet) > 280:
        for i in range(273, -1, -1):
            if tweet[i] == " ":
                tweets.append(tweet[:i])
                tweet = tweet[i:]
                break
    tweets.append(tweet)
    
    # Add counter to each Tweet
    for i in range(len(tweets)):
        tweets[i] = tweets[i] + f" [{i+1}/{len(tweets)}]"

    # Check for repetition
    if " ".join(tweets[-1].split()) == last_tweet:
        print(f"Repeated tweet: {last_tweet}")
        exit()

    # Publish thread
    try:
        id = api.PostUpdate(tweets[0]).id_str
        for tweet in tweets[1:]:
            id = api.PostUpdate(tweet, in_reply_to_status_id=id).id_str
    except twitter.error.TwitterError as err:
        print(err)
else:
    # Check for repetition
    if " ".join(tweet.split()) == last_tweet:
        print(f"Repeated tweet: {last_tweet}")
        exit()

    # Publish Tweet
    try:
        api.PostUpdate(tweet)
    except twitter.error.TwitterError as err:
        print(err)
