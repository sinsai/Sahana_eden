print "Running Tweet request parse script"

def rss2record(entry):
    myd = {}
    myd['ttt_id'] = entry['id']
    myd['link'] = entry['link']	 # url for the entry
    myd['author'] = entry['author']
    myd['tweet'] = entry['title']
    year = entry.updated_parsed[0]
    month = entry.updated_parsed[1]
    day = entry.updated_parsed[2]
    hour = entry.updated_parsed[3]
    minute = entry.updated_parsed[4]
    myd['updated'] = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)
    
    return myd

import datetime
import gluon.contrib.feedparser as feedparser
url_base = "http://epic.cs.colorado.edu:9090/tweets/atom"

N = 50
start = 0
done = False
while done == False:

    #url = url_base + "&limit=" + str(start) + "," + str(N)
    url = url_base
    d = feedparser.parse(url)

    for entry in d.entries:
        rec = rss2record(entry)
        # Don't import duplicates
        if db(db.rms_tweet_request.ttt_id == rec['ttt_id']).count() == 0:
            db.rms_tweet_request.insert(**rec)
        else:
            done = True
            break

    start = start + N

    if len(d["entries"]) == 0:
        done = True

db.commit()
