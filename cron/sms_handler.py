# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import pygsm
import threading
import time
from pygsm.autogsmmodem import GsmModemNotFound

'''
  Module to spawn modem connectivity
'''


class ModemThread( threading.Thread ):
	def __init__(self,modem):
		self.modem = modem
		threading.Thread.__init__ ( self )
	def send_sms(self):
		"""Send Pending SMS from OutBox.
		If succesful then move from OutBox to Sent. A modified copy of send_email"""
		 # Check database for pending mails
		table = db.msg_sms_outbox
		query = table.id > 0
		rows = db(query).select()

		for row in rows:
			contents = row.contents
			# Determine list of users
			group = row.msg_group_id
			table2 = db.msg_group_user
			query = table2.msg_group_id == group
			recipients = db(query).select()
			status = True
			for recipient in recipients:
				to = db(db.pr_person.id==recipient.person_id).select().first().mobile_phone
				if to:
					try:
						self.modem.send_sms(to, contents)
					except:
						status = False
			# We only check status of last recipient
			if status:
				# Add message to Sent
				db.msg_sms_sent.insert(created_by=row.created_by, modified_by=row.modified_by, uuid=row.uuid, msg_group_id=group, contents=contents)
				# Delete from OutBox
				db(table.id==row.id).delete()
				# Explicitly commit DB operations when running from Cron
				db.commit()
		return
		
	def run(self):
		while True:
			self.send_sms()
			time.sleep(2)
			pass
		#self.modem.send_sms("9935648569","Hey!")


modem_configs = db(db.mobile_setting.port != "").select()

# PyGSM GsmModem class instances
modems=[]

for modem in modem_configs:
    # mode is set to text as PDU mode is flaky
    modems.append(pygsm.GsmModem(port=modem.port, baudrate=modem.baud, mode="text")) 

if len(modems) == 0:
    # If no modem is found try autoconfiguring
    try:
      modems.append(pygsm.AutoGsmModem())
    except GsmModemNotFound, e:
      # No way yet to pass back the error yet
      pass

# Starting a thread for each modem we have
for modem in modems:
	ModemThread(modem).run()