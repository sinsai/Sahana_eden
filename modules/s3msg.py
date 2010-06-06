# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__doc__ = \
"""
Module provides api to send messages - Currently SMS and Email

"""

__author__ = "Praneeth Bodduluri <lifeeth[at]gmail.com>"


import urllib

class Msg(object):
	""" Toolkit for hooking into the Messaging framework """
	sms_api_post_config = {}
	sms_api_enabled = False
	def __init__(self, environment, db=None, T=None, mail=None, modem=None):
		self.db = db
		self.sms_api = db(db.mobile_settings.modem_port == "").select().first()
		tmp_parameters = self.sms_api.parameters.split("&")
		self.sms_api_enabled = self.sms_api.enabled
		for tmp_parameter in tmp_parameters:
			self.sms_api_post_config[tmp_parameter.split("=")[0]] = tmp_parameter.split("=")[1]
		self.mail = mail
		self.modem = modem
		
	def send_sms_via_modem(self, mobile, text = ""):
		"""
		Function to send SMS via MODEM
		"""
		self.modem.send_sms(mobile, text)

	def send_sms_via_api(self, mobile, text = ""):
		"""
		Function to send SMS via API
		"""
		self.sms_api_post_config[self.sms_api.message_variable] = text
		self.sms_api_post_config[self.sms_api.to_variable] = str(mobile)
		query = urllib.urlencode(self.sms_api_post_config)
		request = urllib.urlopen(self.sms_api.url, query)
		output = request.read()
		#print output
	
	def send_email_via_api(self, to, subject, message):
		"""
		Wrapper over web2py's email setup
		"""
		self.mail.send(to, subject, message)

	def process_outbox(self, contact_method = 1, option = 1):
		""" Send Pending Messages from OutBox.
		If succesful then move from OutBox to Sent. A modified copy of send_email """
		table = self.db.msg_outbox
		query = ((table.status == 1) & (table.pr_message_method == contact_method))
		rows = self.db(query).select()
		for row in rows:
			status = True
			contents = row.body
			subject = row.subject
			# Determine list of users
			entity = row.pr_pe_id
			table2 = self.db.pr_pentity
			query = table2.id == entity
			entity_type = self.db(query).select().first().opt_pr_entity_type
			def send_pr_pe_id(pr_pe_id):
				table3 = self.db.pr_pe_contact
				query = (table3.pr_pe_id == pr_pe_id) & (table3.opt_pr_contact_method == contact_method)
				recipient = self.db(query).select(table3.value,orderby = table3.priority).first()
				if recipient:
					try:
						if (contact_method == 2 and option == 2):
							self.send_sms_via_modem(recipient.value, contents)
							return True
						if (contact_method == 2 and option == 1):
							self.send_sms_via_api(recipient.value, contents)
							return True
						if (contact_method == 1):
							self.send_email_via_api(recipient.value, subject, contents)
							return True
					except:
						return False
			if entity_type == 2:
				# Group
				table3 = self.db.pr_group
				query = (table3.pr_pe_id == entity)
				group_id = self.db(query).select().first().id
				table4 = self.db.pr_group_membership
				query = (table4.group_id == group_id)
				recipients = self.db(query).select()
				for recipient in recipients:
					person_id = recipient.person_id
					table5 = self.db.pr_person
					query = (table5.id == person_id)
					pr_pe_id = self.db(query).select().first().pr_pe_id
					status = send_pr_pe_id(pr_pe_id)
			if entity_type == 1:
				# Person 
				status = send_pr_pe_id(entity)
				# We only check status of last recipient
			if status:
				# Update status to sent in OutBox
				self.db(table.id == row.id).update(status=2)
				# Explicitly commit DB operations when running from Cron
				self.db.commit()
		return
