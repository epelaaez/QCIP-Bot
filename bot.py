import twitter
import time
import feedparser
import os
import urllib.request as libreq

# Initialize Twitter API
api = twitter.Api(consumer_key=os.environ["CONSUMER_KEY"],
                  consumer_secret=os.environ["CONSUMER_SECRET"],
                  access_token_key=os.environ["ACCESS_TOKEN"],
                  access_token_secret=os.environ["ACCESS_SECRET"])

# Get last Tweets
timeline      = api.GetUserTimeline(user_id=1469787460620193793, screen_name="quantcompinf", count=200)
timeline_text = [" ".join(t.text.split()) for t in timeline]

# Query the arXiv API
arxiv_query = "http://export.arxiv.org/api/query?search_query=cat:quant-ph+AND+%28"
terms       = [
                "gates",
                "information",
                "qubit",
                "bit",
                "stabilizer",
                "algorithm",
                "cryptography",
                "encryption",
                "nisq",
                "transpilation",
                "processor",
                "communication",
                "anneal",
                "code",
                "oracle",
                "circuit",
                "tomography",
                "%22error+correct%22",
                "%22state+preparation%22",
                "%22machine+learning%22",
                "%22neural+network%22",
                "%22bloch+sphere%22"
            ]
for term in terms:
    arxiv_query += f"abs:{term}+OR+"
arxiv_query  = arxiv_query[:-4]
arxiv_query += "%29&sortBy=submittedDate&sortOrder=descending&max_results=10"

# Fetch data and concatenate
with libreq.urlopen(arxiv_query) as url:
    publications = url.read()

for data in feedparser.parse(publications)['entries']:
    title = " ".join(data.title.split()).replace("$", "")

    # Check paper hasn't been shared already
    repeat_flag = False
    for t in timeline_text:
        if title[:80] in t:
            repeat_flag = True
            print("Repeated: ", title)
            break
    if repeat_flag:
        continue

    # Trim author list if greater than 5
    if len(data.authors) < 6:
        auth = ", ".join(author.name for author in data.authors)
    else:
        auth  = ", ".join(data.authors[i].name for i in range(5))
        auth += " et al"
    
    # Retrieve missing data and concatenate it
    summ        = " ".join(data.summary.split()).replace("$", "")
    link        = data.link
    first_tweet = f"{link}\n\n\"{title}\" by {auth}."        
    tweet       = f"Summary: {summ}"
    if len(first_tweet) <= 280:
        tweets = [first_tweet]
    else:
        tweet  = first_tweet + "\n\n" + tweet
        tweets = []

    if len(tweet) > 280:
        # Divide into multiple Tweets for thread
        while len(tweet) > 280:
            for i in range(270, -1, -1):
                if tweet[i] == " ":
                    tweets.append(tweet[:i])
                    tweet = tweet[i:]
                    break
        tweets.append(tweet)
        
        # Add counter to each Tweet
        for i in range(len(tweets)):
            tweets[i] = tweets[i] + f" [{i+1}/{len(tweets)}]"
    else:
        tweets.append(tweet)

    # Publish thread
    ids = []
    try:
        id = api.PostUpdate(tweets[0]).id_str
        ids.append(id)
        time.sleep(0.5)
        for tweet in tweets[1:]:
            id = api.PostUpdate(tweet, in_reply_to_status_id=id).id_str
            ids.append(id)
            time.sleep(0.5)
    except twitter.error.TwitterError as err:
        print(err)
    
    # Check thread was correctly published
    if len(ids) != len(tweets):
        for id in ids:
            api.DestroyStatus(status_id=id)
    else:
        # Check tweets are in reply to each other
        first = api.GetStatus(status_id=ids[0])
        for id in ids[1:]:
            second = api.GetStatus(status_id=id)
            if second.in_reply_to_status_id_str != first:
                for id in ids:
                    api.DestroyStatus(status_id=id)
                break
            else:
                first = second
