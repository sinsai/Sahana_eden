print "Running Tweet request parse script"

def rss2record(item):
    myd = {}
    myd['guid'] = item['guid']
    myd['link'] = item['link']	 # url for the item
    myd['author'] = item['author']
    myd['tweet'] = item['description']
    #year = item.updated_parsed[0]
    #month = item.updated_parsed[1]
    #day = item.updated_parsed[2]
    #hour = item.updated_parsed[3]
    #minute = item.updated_parsed[4]
    #myd['updated'] = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)
    
    return myd

import datetime
import gluon.contrib.feedparser as feedparser
url_base = "http://epic.cs.colorado.edu:9090/tweets/rss"

N = 50
start = 0
done = False
while done == False:

    url = url_base + "&limit=" + str(start) + "," + str(N)
    d = feedparser.parse(url)

    for item in d.items:
        rec, locd = rss2record(item)
        if db(db.rms_tweet_request.ttt_guid == rec['ttt_guid']).count() == 0:
            db.rms_tweet_request.insert(**rec)
        else:
            done = True
            break

    start = start + N

    if len(d["entries"]) == 0:
        done = True

db.commit()
