from selenium import selenium
import unittest, time, re
import actions

class OrganisationTest(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.action = actions.Action()
        self.selenium = selenium("localhost", 4444, "*chrome", "http://127.0.0.1:8000/")
        self.selenium.start()
    
    def create_organisation(self, name, acronym, type, cluster, country, website):
        sel = self.selenium

        name = name.strip()
        acronym = acronym.strip()
        type = type.strip()
        cluster = cluster.strip()
        country = country.strip()
        website = website.strip()
        
        sel.open("eden/org/organisation/create")
        self.assertEqual("Add Organization", sel.get_text("//h2"))
        sel.type("org_organisation_name", name)
        sel.type("org_organisation_acronym", acronym)
        sel.select("org_organisation_type", "label="+type)
        sel.click("//option[@value='10']")
        sel.select("org_organisation_cluster_id", "label="+cluster)
        sel.select("org_organisation_country", "label="+country)
        sel.type("org_organisation_website", website)
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        time.sleep(1)
        self.assertEqual("Organization added", sel.get_text("//div[@class=\"confirmation\"]"))
        self.assertEqual("List Organizations", sel.get_text("//h2"))
        
    def test_organzation(self):
        sel = self.selenium
        sel.open("/eden/default/index")
        sel.click("link=Organisation Registry")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Add")
        sel.wait_for_page_to_load("30000")
        time.sleep(1)
        self.assertEqual("Not Authorised", sel.get_text("//div[@class=\"error\"]"))
        self.assertEqual("Login", sel.get_text("//h2"))
        self.action.login(self, "testing@example.com", "testing" )
        
        source = open("../data/organisation.txt", "r")
        values = source.readlines()
        source.close()
        for org in values:
            details = org.split(',')
            if len(details) == 6:
                self.create_organisation(details[0].strip(),
                                         details[1].strip(),
                                         details[2].strip(),
                                         details[3].strip(),
                                         details[4].strip(),
                                         details[5].strip(),
                                         )
#        self.create_organisation("Example.com", "eCom", "Private", "Logistics", "United Kingdom", "www.example.com")
#        self.create_organisation("Example.net", "eNet", "International NGO", "Recovery", "United States", "www.example.net")
    
    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
