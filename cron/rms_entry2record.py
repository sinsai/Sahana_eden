print "Running Script"

def rss2record(entry):
	myd = {}
	myd['ush_id'] = entry['id']
	myd['link'] = entry['link']	 # url for the entry
 	myd['author'] = entry['author']
	year = entry.updated_parsed[0]
	month = entry.updated_parsed[1]
	day = entry.updated_parsed[2]
	hour = entry.updated_parsed[3]
	minute = entry.updated_parsed[4]
	myd['updated'] = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)
	myd['title'] = entry['title']
	myd['sms'] = entry['sms']
	myd['smsrec'] = entry['smsrec']
	myd['phone']=entry['phone']
	myd['categorization'] = entry['categorization'] 
	myd['firstname'] = entry['firstname'] 
	myd['lastname'] = entry['lastname']
	myd['status'] = entry['status']
	myd['address'] = entry['address']
	myd['city'] = entry['city']
	myd['department'] = entry['department']
	myd['summary'] = entry['summary']
	myd['notes'] = entry['notes']
	gpoint = entry['georss_point'].split()
	myd['lat'] = gpoint[0]
	myd['long'] = gpoint[1]
	return myd

# d.entries[0]['updated_parsed']

import datetime
import gluon.contrib.feedparser as feedparser
d = feedparser.parse("http://75.101.195.137/rss.php?key=yqNm7FHSwfdRb8nC2653")
for entry in d.entries:
	rec = rss2record(entry)
        if db(db.rms_sms_request.ush_id == rec['ush_id']).count() == 0:
		db.rms_sms_request.insert(**rec)

db.commit()
