def test_b():
    assert 'b' == 'b'

class TestExampleTwo:
    def test_c(self):
        assert 'c' == 'c'

import unittest
        
class ExampleTest(unittest.TestCase):
    def test_a(self):
        self.assert_(1 == 1)
