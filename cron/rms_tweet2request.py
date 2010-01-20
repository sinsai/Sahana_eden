print "Running Tweet request parse script"

def rss2record(entry):
    myd = {}

    myd['link'] = entry['link']	 # url for the entry
    myd['author'] = entry['author']
    myd['tweet'] = entry['title']
    year = entry.updated_parsed[0]
    month = entry.updated_parsed[1]
    day = entry.updated_parsed[2]
    hour = entry.updated_parsed[3]
    minute = entry.updated_parsed[4]
    myd['updated'] = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)

    myd['ttt_id'] = entry['link'].split('/')[-1]

    return myd

import datetime
import gluon.contrib.feedparser as feedparser
url = "http://epic.cs.colorado.edu:9090/tweets/atom"
d = feedparser.parse(url)

for entry in d.entries:

    rec = rss2record(entry)

    if db(db.rms_tweet_request.ttt_id == rec['ttt_id']).count() == 0:
        db.rms_tweet_request.insert(**rec)
    else:
        break

db.commit()
