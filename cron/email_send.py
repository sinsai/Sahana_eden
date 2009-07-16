import urllib
#urllib.urlopen('http://%s/sahana/msg/email_send' % request.env.http_host).read() 
urllib.urlopen('http://127.0.0.1:8000/sahana/msg/email_send').read()
