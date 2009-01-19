import wsgi_intercept.webtest_intercept

class WSGI_Test(wsgi_intercept.webtest_intercept.WebCase):
    "Class to use for Testing Sahana in DocTests"
    HTTP_CONN = wsgi_intercept.WSGI_HTTPConnection
    HOST='localhost'
    PORT=8001
    def setUp(self):
        wsgi_intercept.add_wsgi_intercept(self.HOST, self.PORT, create_fn)
