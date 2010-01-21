print "Running Tweet request parse script"

db.rms_tweet_request.truncate()

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

    # The twitter id is NOT stored in the ID field, you have to
    # extract if from the end of the link
    myd['ttt_id'] = entry['link'].split('/')[-1]
    #myd['ttt_id'] = ":".join(entry['id'].split(':')[-2:])

    return myd

import datetime
import gluon.contrib.feedparser as feedparser
url_base = "http://epic.cs.colorado.edu:9090/tweets/atom"

count = 0

N = 100
start = 0
done = False
while done == False:
    
    print "Extracting RSS Entries: %6i through %6i" % (start, start+N-1)
    url = url_base + "?limit=" + str(start) + "," + str(N)
    d = feedparser.parse(url)

    for entry in d.entries:
        rec = rss2record(entry)
        
        # Make sure there are no duplicate entries before we add it:
        if db(db.rms_tweet_request.ttt_id == rec['ttt_id']).count() == 0:
            db.rms_tweet_request.insert(**rec)
            count += 1
        #else:
        #    done = True
        #    break

    start += N
    if len(d.entries) == 0:
        done = True

print count
db.commit()
