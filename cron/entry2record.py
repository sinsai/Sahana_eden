import datetime
import gluon.contrib.feedparser as feedparser

def rss2record(entry):
	myd = {}
	myd['title'] = entry['title']
	myd['link'] = entry['link']	 # url for the entry
	myd['comment'] = entry['summary']
	year = entry.updated_parsed[0]
	month = entry.updated_parsed[1]
	day = entry.updated_parsed[2]
	hour = entry.updated_parsed[3]
	minute = entry.updated_parsed[4]
	myd['pubdate'] = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)
	myd['guid'] = entry['id'] # Ushahidi URL
	myd['georss'] = entry['georss_point'] # string for lat and long
	# parse from website
	myd['verified'] = False
	return myd

d = feedparser.parse("http://haiti.ushahidi.com/feed")

for entry in d.entries:
	rec = rss2record(entry)
	db.rms_aid_request.insert(**rec)

db.commit()
