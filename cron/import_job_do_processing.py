# -*- coding: utf-8 -*-

# This script process import_job records from the admin module that are in the
# 'processing' state. This indicates that the user has matched up the columns
# and the records are ready to be validated and prepared for import.
#

jobs = db(db.admin_input_job.status == 'processing').select()
for job in jobs:
    # Get job column map.
    try:
        column_map = pickle.loads(job.column_map)
    except pickle.UnpicklingError:
        column_map = []
    
    # Open the input file.
    filepath = os.path.join(request.folder, 'uploads', filename)
    reader = csv.reader(open(filepath, 'r'))
    
    # Retrieve column headings from the first line.
    csv_headings = []
    for line in reader:
        for col in line:
            csv_headings.append(col)
        break
    if csv_headings != [t[0] for t in column_map]:
        print 'Cannot process job #%d. Column headings do not match DB!' % job.id
        continue

    # Read each line
    for line_num, line in enumerate(reader, 0):
        line_data = {}
        for idx, col in enumerate(line):
            field = column_map[idx][1]
            if not field:
                continue
            line_data[field] = col
        print line_data

    # Map CSV headers to model fields
    # validate via SQLFORM
    # store field, value pairs and validity status into an ImportLine model.
    pass

# Explicitly commit DB operations when running from Cron
db.commit()
