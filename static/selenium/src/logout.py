"""
No description.
"""

S.open('/eden/default/login/')
S.clickAndWait('link=Logout')
S.verifyTextPresent('Logged Out')
