import os
import tempfile
import unittest
import sys


if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as tmp:
        os.environ['OCFL_ROOT'] = tmp
        loader = unittest.TestLoader()
        tests = loader.discover(start_dir='.')
        test_runner = unittest.TextTestRunner()
        result = test_runner.run(tests)
    if result.errors or result.failures:
        sys.exit(1)
    else:
        sys.exit(0)
