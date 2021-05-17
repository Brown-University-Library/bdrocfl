import os
import unittest
from bdrocfl import ocfl


class TestOcfl(unittest.TestCase):

    def test_1(self):
        self.assertEqual(ocfl.object_path('testsuite:abcd1234'), os.path.join(ocfl.OCFL_ROOT, '1b5', '64f', '1ff', 'testsuite%3aabcd1234'))
