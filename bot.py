import twitter
import feedparser
import os
import urllib.request as libreq

# Initialize Twitter API
api = twitter.Api(consumer_key=os.environ["CONSUMER_KEY"],
                  consumer_secret=os.environ["CONSUMER_SECRET"],
                  access_token_key=os.environ["ACCESS_TOKEN"],
                  access_token_secret=os.environ["ACCESS_SECRET"])

# Query the arXiv API
arxiv_query = "http://export.arxiv.org/api/query?search_query=cat:quant-ph+AND+%28"
terms       = ["gates", "compute", "computation", "information", "qubit", "bit", "algorithm", "%22error+correct%22", "cryptography", "encryption", "data", "nisq", "transpilation", "processor", "communication", "anneal", "code", "circuit", "%22machine+learning%22", "%22neural+network%22", "oracle"]
for term in terms:
    arxiv_query += f"abs:{term}+OR+"
arxiv_query  = arxiv_query[:-4]
arxiv_query += "%29&sortBy=lastUpdatedDate&sortOrder=descending&max_results=1"

# Fetch data and concatenate
with libreq.urlopen(arxiv_query) as url:
    publications = url.read()
data  = feedparser.parse(publications)['entries'][0]
title = data.title
link  = data.link
summ  = data.summary
auth  = ', '.join(author.name for author in data.authors)
tweet = " ".join(f"\"{title}\" by {auth}. Summary: {summ} {link}.".split())
tweet = ''.join(c for c in tweet if c not in set("\$"))

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

    # Publish thread
    try:
        id = api.PostUpdate(tweets[0]).id_str
        for tweet in tweets[1:]:
            id = api.PostUpdate(tweet, in_reply_to_status_id=id).id_str
    except twitter.error.TwitterError as err:
        print(err)
else:
    # Publish Tweet
    try:
        api.PostUpdate(tweet)
    except twitter.error.TwitterError as err:
        print(err)
