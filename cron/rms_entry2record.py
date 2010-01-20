print "Running SMS request parse script"

db.rms_sms_request.truncate()
db.media_metadata.truncate()
db.gis_location.truncate()

marker  = db(db.gis_marker.name=="phone").select()
feature = db(db.gis_feature_class.name=="SMS").select()

marker_id = marker[0]['id'] if len(marker) == 1 else None
feature_id = feature[0]['id'] if len(feature) == 1 else None

def rss2record(entry):
    myd = {}
    locd = {}

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
    myd['actionable'] = True if entry['actionable'] != '0' else False

    # Fix escape characters: 
    myd["notes"] = " ".join(myd["notes"].split())
    myd["notes"] = myd["notes"].replace('\\"', '"')
    myd["notes"] = myd["notes"].replace("\\'", "'")

    # Add location information. The key name contains a colon, and for
    # this reason, is platform dependent. Thus, we just look for any
    # entry that ends in "point":
    for key in entry.keys():
        if key[-5:] == "point":
            # Found the location info
            gpoint = entry[key].split()
            lat = float(gpoint[0])
            lon = float(gpoint[1])

            # Ushahidi uses a 0,0 lat/lon to indicate no lat lon.
            if abs(lat) > 1.0e-8 and abs(lon) > 1.0e-8:
                locd['lat' ] = lat
                locd['lon' ] = lon
                name = "SMS: "
                if myd['categorization'] != "":
                    name += myd['categorization']
                else: 
                    name += "No category"

                locd['name'] = name

                if marker_id is not None:
                    locd['marker_id'] = marker_id
                if feature_class_id is not None:
                    locd['feature_class_id'] = feature_id


    return myd, locd

import datetime
import gluon.contrib.feedparser as feedparser
url_base = "http://75.101.195.137/rss.php?key=yqNm7FHSwfdRb8nC2653"

ids = []

N = 100
start = 0
done = False
while done == False:

    url = url_base + "&limit=" + str(start) + "," + str(N)
    d = feedparser.parse(url)

    for entry in d.entries:
        rec, locd = rss2record(entry)
        # Don't import duplicates
        if db(db.rms_sms_request.ush_id == rec['ush_id']).count() == 0:

            locid = None
            if locd != {}:
                # Calculate WKT for display on Map
                locd['wkt'] = 'POINT(%f %f)' % (locd['lon'], locd['lat'])
                locid = db.gis_location.insert(**locd)

            rec["location_id"] = locid
            smsid = db.rms_sms_request.insert(**rec)
            if locid != None:
                ids.append((smsid,locid))

            # Add media_metadata entry to show additional
            # information on the map
            metadata = {}
            metadata["event_time" ] = rec["updated"]

            desc = rec["sms"]

            # If there is a note, append it to the description:
            if rec["notes"] != "":
                # New lines, apstrophes, and quotes break the mapping.
                rec["notes"] = " ".join(rec["notes"].split())
                rec["notes"] = rec["notes"].replace('"', '\\"')
                rec["notes"] = rec["notes"].replace("'", "\\'")

                #rec["notes"] = rec["notes"].replace('\\', '\\\\')
                #rec["notes"] = rec["notes"].replace('\\\\"', '\\"')
                #rec["notes"] = rec["notes"].replace("\\\\'", "\\'")

                desc = rec["sms"] + " NOTE: " + rec["notes"]

            metadata["description"] = desc
            metadata["location_id"] = locid
            db.media_metadata.insert(**metadata)
        else:
            done = True
            break

    start = start + N
    
    if len(d["entries"]) == 0:
        done = True

db.commit()

# Now loop through and set the location names with the sms id numbers:
for smsid, locid in ids:
    db(db.gis_location.id == locid).update(name="SMS " + repr(smsid))

db.commit()
