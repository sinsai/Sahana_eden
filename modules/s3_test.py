import wsgi_intercept.webtest_intercept

class WSGI_Test(wsgi_intercept.webtest_intercept.WebCase):
    "Class to use for Testing Sahana in DocTests"
    HTTP_CONN = wsgi_intercept.WSGI_HTTPConnection
    HOST='localhost'
    PORT=8000
    
    def __init__(self,db):
        self.db=db

    def setUp(self):
        # Not working :/
        #self.shn_create_testdata(db)
        wsgi_intercept.add_wsgi_intercept(self.HOST, self.PORT, create_fn)

    def runTest(self):
        "Mandatory method for all TestCase instances"
        return

    def shn_create_testdata(self,db):
        "Create test Data for all modules"
        self.shn_create_testdata_cr(db)
        return

    def shn_create_testdata_cr(self,db):
        "Create test Data for Shelter Registry"
        module='cr'
        resource='shelter'
        table=module+'_'+resource
        if not len(db().select(db[table].ALL)):
            db[table].insert(
                name="Test Shelter",
            description="Just a test",
            location_id=1,
            person_id=1,
            address='52 Test Street',
            capacity=100,
            dwellings=10,
            persons_per_dwelling=10,
            area='1 sq km'
            )
