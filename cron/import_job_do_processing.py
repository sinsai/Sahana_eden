# -*- coding: utf-8 -*-

# This script process import_job records from the admin module that are in the
# 'processing' state. This indicates that the user has matched up the columns
# and the records are ready to be validated and prepared for import.
#

jobs = db(db.admin_input_job.status == 'processing').select()
for job in jobs:
    # Read each line
    # Map CSV headers to model fields
    # validate via SQLFORM
    # store field, value pairs and validity status into an ImportLine model.
    pass

# Explicitly commit DB operations when running from Cron
db.commit()
