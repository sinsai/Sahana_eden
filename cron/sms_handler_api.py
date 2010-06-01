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
This is the async cron daemon for handling outgoing SMS.

"""

__author__ = "Praneeth Bodduluri <lifeeth[at]gmail.com>"

import urllib

api_configs = db(db.mobile_settings.modem_port == '').select()
config={}
api = api_configs[0]	
url = api.url
parameters = api.parameters.split('&')

for parameter in parameters:
	config[parameter.split('=')[0]] = parameter.split('=')[1]
to_variable = api.to_variable
message_variable = api.message_variable

def send_sms_api(mobile,text = ''):
	"""
		Function to send SMS via API
	"""
	config[message_variable] = text
	config[to_variable] = str(mobile)
	query = urllib.urlencode(config)
	request = urllib.urlopen(url, query)
	output = request.read()
	#print output
	
send_sms_api(9935648569,"Hello")