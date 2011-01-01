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
    Module providing an API to send messages
    - Currently SMS, Email & Twitter
    
    pr_message_method:
    1: Email
    2: SMS
    4: Twitter
    
   Messages get sent to the Outbox (& Log)
   From there, Cron tasks collect them & send them

"""

__author__ = "Praneeth Bodduluri <lifeeth[at]gmail.com>"

__all__ = ["S3Msg"]

import sys
import string
import urllib
from urllib2 import urlopen
from s3utils import s3_debug

try:
    import tweepy
except ImportError:
    s3_debug("Tweepy not available, so non-Tropo Twitter support disabled")

IDENTITYTRANS = ALLCHARS = string.maketrans("", "")
NOTPHONECHARS = ALLCHARS.translate(IDENTITYTRANS, string.digits)
NOTTWITTERCHARS = ALLCHARS.translate(IDENTITYTRANS, string.digits + string.letters + '_')

TWITTER_MAX_CHARS = 140
TWITTER_HAS_NEXT_SUFFIX = u' \u2026'
TWITTER_HAS_PREV_PREFIX = u'\u2026 '

class S3Msg(object):
    """ Toolkit for hooking into the Messaging framework """

    def __init__(self, environment, deployment_settings, db=None, T=None, mail=None, modem=None):
        try:
            self.deployment_settings = deployment_settings
            self.db = db
            self.mail = mail
            self.modem = modem

        except:
            pass

    def sanitise_phone(self, phone):
        """
            Strip out unnecessary characters from the string:
            +()- & space
        """

        deployment_settings = self.deployment_settings
        default_country_code = deployment_settings.get_L10n_default_country_code()

        clean = phone.translate(IDENTITYTRANS, NOTPHONECHARS)

        # If number starts with a 0 then need to remove this & add the country code in
        if clean[0] == "0":
            # Add default country code
            if default_country_code == 39:
                # Italy keeps 0 after country code
                clean = str(default_country_code) + clean
            else:
                clean = str(default_country_code) + string.lstrip(clean, "0")

        return clean

    def send_sms_via_modem(self, mobile, text=""):
        """
            Function to send SMS via locally-attached Modem
        """

        mobile = self.sanitise_phone(mobile)

        # Add '+' before country code
        mobile = "+" + mobile

        try:
            self.modem.send_sms(mobile, text)
            return True
        except:
            return False

    def send_sms_via_api(self, mobile, text=""):
        """
            Function to send SMS via API
        """

        db = self.db

        sms_api = db(db.msg_gateway_settings.enabled == True).select(limitby=(0, 1)).first()
        if sms_api:
            tmp_parameters = sms_api.parameters.split("&")
            for tmp_parameter in tmp_parameters:
                sms_api_post_config[tmp_parameter.split("=")[0]] = tmp_parameter.split("=")[1]

        mobile = self.sanitise_phone(mobile)

        try:
            sms_api_post_config[sms_api.message_variable] = text
            sms_api_post_config[sms_api.to_variable] = str(mobile)
            query = urllib.urlencode(sms_api_post_config)
            request = urllib.urlopen(sms_api.url, query)
            output = request.read()
            return True
        except:
            return False

    def sanitise_twitter_account(self, account):
        """
            Only keep characters that are legal for a twitter account:
            letters, digits, and _
        """

        return account.translate(IDENTITYTRANS, NOTTWITTERCHARS)

    def break_to_chunks(self, text,
                        chunk_size=TWITTER_MAX_CHARS,
                        suffix = TWITTER_HAS_NEXT_SUFFIX,
                        prefix = TWITTER_HAS_PREV_PREFIX):
        """
            Breaks text to <=chunk_size long chunks. Tries to do this at a space.
            All chunks, except for last, end with suffix.
            All chunks, except for first, start with prefix.
        """

        res = []
        current_prefix = "" # first chunk has no prefix
        while text:
            if len(current_prefix + text) <= chunk_size:
                res.append(current_prefix + text)
                return res
            else: # break a chunk
                c = text[:chunk_size - len(current_prefix) - len(suffix)]
                i = c.rfind(" ")
                if i > 0: # got a blank
                    c = c[:i]
                text = text[len(c):].lstrip()
                res.append((current_prefix + c.rstrip() + suffix))
                current_prefix = prefix # from now on, we want a prefix

    def get_twitter_api():
        """
            Initialize Twitter API
        """

        db = self.db
        deployment_settings = self.deployment_settings

        twitter_settings = db(db.msg_twitter_settings.id > 0).select(limitby=(0, 1)).first()
        if twitter_settings and twitter_settings.twitter_account:
            try:
                oauth = tweepy.OAuthHandler(deployment_settings.twitter.oauth_consumer_key,
                                            deployment_settings.twitter.oauth_consumer_secret)
                oauth.set_access_token(twitter_settings.oauth_key,
                                       twitter_settings.oauth_secret)
                twitter_api = tweepy.API(oauth)
                twitter_account = tmp_twitter_settings.twitter_account
                return dict(twitter_api=twitter_api, twitter_account=twitter_account)
            except:
                pass

        return None
    
    def send_text_via_twitter(self, recipient, text=""):
        """
            Function to send text to recipient via direct message (if recipient follows us).
            Falls back to @mention (leaves less characters for the message).
            Breaks long text to chunks if needed.
        """

        # Initialize Twitter API
        twitter_settings = self.get_twitter_api()

        twitter_api = None
        if twitter_settings:
            twitter_api = twitter_settings["twitter_api"]
            twitter_account = twitter_settings["twitter_account"]
        
        if not twitter_api and text:
            # Abort
            return False

        recipient = self.sanitise_twitter_account(recipient)
        try:
            can_dm = twitter_api.exists_friendship(recipient, twitter_account)
        except tweepy.TweepError: # recipient not found
            return False
        if can_dm:
            chunks = self.break_to_chunks(text, TWITTER_MAX_CHARS)
            for c in chunks:
                try:
                    # Note: send_direct_message() requires explicit kwargs (at least in tweepy 1.5)
                    # See http://groups.google.com/group/tweepy/msg/790fcab8bc6affb5
                    twitter_api.send_direct_message(screen_name=recipient, text=c)
                except tweepy.TweepError:
                    s3_debug("Unable to Tweet DM")
        else:
            prefix = "@%s " % recipient
            chunks = self.break_to_chunks(text, TWITTER_MAX_CHARS - len(prefix))
            for c in chunks:
                try:
                    twitter_api.update_status(prefix + c)
                except tweepy.TweepError:
                    s3_debug("Unable to Tweet @mention")
        return True

    #-------------------------------------------------------------------------------------------------     
    def send_text_via_tropo(self, row_id, message_id, recipient, message, network = "SMS"):
        """
            Send a URL request to Tropo to pick a message up
        """

        db = self.db

        base_url = "http://api.tropo.com/1.0/sessions"
        action = "create"

        tropo_settings = db(db.msg_tropo_settings.id == 1).select(db.msg_tropo_settings.token_messaging,
                                                                  limitby=(0, 1)).first()
        if tropo_settings:
            tropo_token_messaging = tropo_settings.token_messaging
            #tropo_token_voice = tropo_settings.token_voice
        else:
            return

        if network == "SMS":
            recipient = self.sanitise_phone(recipient)

        try:
            db.msg_tropo_scratch.insert(row_id = row_id,
                                        message_id = message_id,
                                        recipient = recipient,
                                        message = message,
                                        network = network)
            params = urllib.urlencode([("action", action),
                                       ("token", tropo_token_messaging),
                                       ("outgoing", "1"),
                                       ("row_id", row_id)
                                      ])
            xml = urlopen("%s?%s" % (base_url, params)).read()
            # Parse Response (actual message is sent as a response to the POST which will happen in parallel)
            #root = etree.fromstring(xml)
            #elements = root.getchildren()
            #if elements[0].text == "false":
            #    session.error = T("Message sending failed! Reason:") + " " + elements[2].text
            #    redirect(URL(r=request, f="index"))
            #else:
            #    session.flash = T("Message Sent")
            #    redirect(URL(r=request, f="index"))
        except:
            pass
        return False # Returning False because the API needs to ask us for the messsage again.


    def send_email_via_api(self, to, subject, message):
        """
            Function to send Email via API
            - simple Wrapper over Web2Py's Email API
        """

        return self.mail.send(to, subject, message)

    def send_by_pe_id(self,
                      pe_id,
                      subject="",
                      message="",
                      sender_pe_id = None,
                      pr_message_method = 1,
                      sender="",
                      fromaddress="",
                      system_generated = False):
        """
            Send a message to a Person Entity
            - depends on pr_message_method
        """

        db = self.db

        try:
            message_log_id = db.msg_log.insert(pe_id = sender_pe_id,
                                               subject = subject,
                                               message = message,
                                               sender  = sender,
                                               fromaddress = fromaddress)
        except:
            return False
            #2) This is not transaction safe - power failure in the middle will cause no message in the outbox

        if isinstance(pe_id, list):
            listindex = 0
            for prpeid in pe_id:
                try:
                    db.msg_outbox.insert(message_id = message_log_id,
                                         pe_id = prpeid,
                                         pr_message_method = pr_message_method,
                                         system_generated = system_generated)
                    listindex = listindex + 1
                except:
                    return listindex
        else:
            try:
                db.msg_outbox.insert(message_id = message_log_id,
                                     pe_id = pe_id,
                                     pr_message_method = pr_message_method,
                                     system_generated = system_generated)
            except:
                return False
        # Explicitly commit DB operations when running from Cron
        db.commit()
        return True

    def send_email_by_pe_id(self,
                            pe_id,
                            subject="",
                            message="",
                            sender_pe_id=None,  # s3_logged_in_person() is useful here
                            sender="",
                            fromaddress="",
                            system_generated=False):
        """
            API wrapper over send_by_pe_id
            - depends on pr_message_method
        """

        return self.send_by_pe_id(pe_id,
                                  subject,
                                  message,
                                  sender_pe_id,
                                  1, # To set as an email
                                  sender,
                                  fromaddress,
                                  system_generated)

    def send_sms_by_pe_id(self,
                          pe_id,
                          message="",
                          sender_pe_id=None,  # s3_logged_in_person() is useful here
                          sender="",
                          fromaddress="",
                          system_generated=False):
        """
            API wrapper over send_by_pe_id
            - depends on pr_message_method
        """

        return self.send_by_pe_id(pe_id,
                                  message,
                                  sender_pe_id,
                                  2, # To set as an SMS
                                  sender,
                                  fromaddress,
                                  system_generated,
                                  subject=""
                                 )

    def process_outbox(self, contact_method=1, option=1): #pr_message_method dependent
        """
            Send Pending Messages from Outbox.
            If succesful then move from Outbox to Sent. A modified copy of send_email
        """

        db = self.db
        settings = db(db.msg_setting.id > 0).select(limitby=(0, 1)).first()
        outgoing_sms_handler = settings.outgoing_sms_handler

        table = db.msg_outbox
        query = ((table.status == 1) & (table.pr_message_method == contact_method))
        rows = db(query).select()
        chainrun = False # Used to fire process_outbox again - Used when messages are sent to groups
        for row in rows:
            status = True
            message_id = row.message_id
            logrow = db(db.msg_log.id == message_id).select(limitby=(0, 1)).first()
            # Get message from msg_log
            message = logrow.message
            subject = logrow.subject
            sender_pe_id = logrow.pe_id
            # Determine list of users
            entity = row.pe_id
            table2 = db.pr_pentity
            query = table2.id == entity
            entity_type = db(query).select(table2.instance_type, limitby=(0, 1)).first().instance_type
            def dispatch_to_pe_id(pe_id):
                table3 = db.pr_pe_contact
                query = (table3.pe_id == pe_id) & (table3.contact_method == contact_method) & (table3.deleted == False)
                recipient = db(query).select(table3.value, orderby = table3.priority, limitby=(0, 1)).first()
                if recipient:
                    if (contact_method == 4):
                        return self.send_text_via_twitter(recipient.value, message)
                    if (contact_method == 2 and option == 2):
                        if outgoing_sms_handler == "Modem":
                            return self.send_sms_via_modem(recipient.value, message)
                        else:
                            return False
                    if (contact_method == 2 and option == 1):
                        if outgoing_sms_handler == "Gateway":
                            return self.send_sms_via_api(recipient.value, message)
                        else:
                            return False
                    if (contact_method == 2 and option == 3):
                        if outgoing_sms_handler == "Tropo":
                            return self.send_text_via_tropo(row.id, message_id, recipient.value, message) # This does not mean the message is sent
                        else:
                            return False
                    if (contact_method == 1):
                        return self.send_email_via_api(recipient.value, subject, message)
                return False

            if entity_type == "pr_group":
                # Take the entities of it and add in the messaging queue - with
                # sender as the original sender and marks group email processed
                # Set system generated = True
                table3 = db.pr_group
                query = (table3.pe_id == entity)
                group_id = db(query).select(table3.id, limitby=(0, 1)).first().id
                table4 = db.pr_group_membership
                query = (table4.group_id == group_id)
                recipients = db(query).select(table4.person_id)
                for recipient in recipients:
                    person_id = recipient.person_id
                    table5 = db.pr_person
                    query = (table5.id == person_id)
                    pe_id = db(query).select(table5.pe_id, limitby=(0, 1)).first().pe_id
                    db.msg_outbox.insert(message_id = message_id,
                                         pe_id = pe_id,
                                         pr_message_method = contact_method,
                                         system_generated = True)
                status = True
                chainrun = True
            
            elif entity_type == "org_organisation":
                # Take the entities of it and add in the messaging queue - with
                # sender as the original sender and marks group email processed
                # Set system generated = True
                table3 = db.org_organisation
                query = (table3.pe_id == entity)
                org_id = db(query).select(table3.id, limitby=(0, 1)).first().id
                table4 = db.org_staff
                query = (table4.organisation_id == org_id)
                recipients = db(query).select(table4.person_id)
                for recipient in recipients:
                    person_id = recipient.person_id
                    table5 = db.pr_person
                    query = (table5.id == person_id)
                    pe_id = db(query).select(table5.pe_id, limitby=(0, 1)).first().pe_id
                    db.msg_outbox.insert(message_id = message_id,
                                         pe_id = pe_id,
                                         pr_message_method = contact_method,
                                         system_generated = True)
                status = True
                chainrun = True

            if entity_type == "pr_person":
                # Person
                status = dispatch_to_pe_id(entity)

            if status:
                # Update status to sent in Outbox
                db(table.id == row.id).update(status=2)
                # Set message log to actioned
                db(db.msg_log.id == message_id).update(actioned=True)
                # Explicitly commit DB operations when running from Cron
                db.commit()

        if chainrun :
            self.process_outbox(contact_method, option)

        return


    #-------------------------------------------------------------------------    
    def receive_subscribed_tweets(self):
        """
            Function  to call to drop the tweets into search_results table - called via cron
        """
        
        # Initialize Twitter API
        twitter_settings = self.get_twitter_api()

        twitter_api = None
        if twitter_settings:
            twitter_api = twitter_settings["twitter_api"]
        
        if not twitter_api:
            # Abort
            return False

        db = self.db
        table = db.msg_twitter_search
        rows = db().select(table.ALL)     
                
        results_table = db.msg_twitter_search_results
        
        # Get the latest updated post time to use it as since_id in twitter search
        recent_time = results_table.posted_by.max()

        for row in rows:
            query = row.search_query 
            try:
                if recent_time:
                    search_results = twitter_api.search(query, result_type="recent", show_user=True, since_id=recent_time)
                else:
                    search_results = twitter_api.search(query, result_type="recent", show_user=True)

                search_results.reverse()

                for result in search_results:
                    # Check if the tweet already exists in the table
                    tweet_exists = db((results_table.posted_by == result.from_user) & (results_table.posted_at == result.created_at )).select().first()  
                    
                    if tweet_exists:
                        continue
                    else:
                        results_table.insert(tweet = result.text,
                                             posted_by = result.from_user,
                                             posted_at = result.created_at,
                                             twitter_search = row.id
                                            ) 
            except tweepy.TweepError:
                s3_debug("Unable to get the Tweets for the user search query.")
                return False

            # Explicitly commit DB operations when running from Cron
            db.commit()
            
        return True

    #------------------------------------------------------------------------
    def receive_msg(self,
                    subject="",
                    message="",
                    sender="",
                    fromaddress="",
                    system_generated = False,
                    pr_message_method = 1,
                   ):
        """
            Function to call to drop incoming messages into msg_log
        """

        db = self.db

        try:
            message_log_id = db.msg_log.insert(inbound = True,
                                               subject = subject,
                                               message = message,
                                               sender  = sender,
                                               fromaddress = fromaddress,
                                               )
        except:
            return False
            #2) This is not transaction safe - power failure in the middle will cause no message in the outbox
        try:
            db.msg_channel.insert(message_id = message_log_id,
                                  pr_message_method = pr_message_method)
        except:
            return False
        # Explicitly commit DB operations when running from Cron
        db.commit()
        return True
