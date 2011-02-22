from sahanaTest import SahanaTest
import unittest, re

class HospitalTest(SahanaTest):
    """ Test the Hospital Management System """
    _sortList = ("checkAuthentication",
                 "CreateHospital"
                )


    def firstRun(self):
        sel = HospitalTest.selenium
        HospitalTest.hospitals = []


    def create_hospital(self, gov_uuid, name, type):
        sel = HospitalTest.selenium

        gov_uuid = gov_uuid.strip()
        name = name.strip()

        sel.open("hms/hospital/create")
        self.assertEqual("Add Hospital", sel.get_text("//h2"))
        sel.type("hms_hospital_gov_uuid", gov_uuid)
        sel.type("hms_hospital_name", name)
        sel.select("hms_hospital_facility_type", "label=%s" % type)
        sel.click("//input[@value='Save']")

        sel.wait_for_page_to_load("30000")
        self.assertTrue(self.action.successMsg("Hospital information added"), "failed to add hospital %s" % name)
        self.assertEqual("List Hospitals", sel.get_text("//h2"))
        print "Hospital %s created" % (name)

    def addHospital(self):
        sel = HospitalTest.selenium
        source = open("../data/hospital.txt", "r")
        values = source.readlines()
        source.close()
        for hospital in values:
            details = hospital.split(",")
            if len(details) == 3:
                self.create_hospital(details[0].strip(), # gov_uuid
                                     details[1].strip(), # name
                                     details[2].strip()  # facility_type
                                     )
                HospitalTest.hospitals.append(details[0].strip())

    def checkAuthentication(self):
        sel = HospitalTest.selenium
        self.action.logout()
        sel.open("hms/hospital/create")
        self.action.errorMsg("Authentication Required")
        self.assertEqual("Login", self.selenium.get_text("//h2"))

    def CreateHospital(self):
        # Log in as admin an then move to the add hospital page
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        # Add the test hospitals
        self.addHospital()
        """ Test to check the elements of the create hospital form """
        sel = HospitalTest.selenium
        sel.open("hms/hospital/create")
        # check that the UI controls are present
        self.action.checkForm (
                   (
                    ("input", "hms_hospital_gov_uuid"),
                    ("input", "hms_hospital_name"),
                    ("select", "hms_hospital_facility_type"),
                   ),
                   ("Save",),("Government UID",)
                  )

    def lastRun(self):
        # Delete the test hospitals
        sel = HospitalTest.selenium
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        sel.open("hms/hospital")
        for hospital in HospitalTest.hospitals:
            self.action.searchUnique(hospital)
            sel.click("link=Delete")
            self.assertTrue(re.search(r"^Sure you want to delete this object[\s\S]$", sel.get_confirmation()))
            self.action.successMsg("Hospital deleted")

if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
    HospitalTest.selenium.stop()
