from datetime import datetime, timezone
import json
import os
import shutil
import unittest
from bdrocfl import ocfl


SIMPLE_INVENTORY = {
  "digestAlgorithm": "sha512",
  "head": "v3",
  "id": "testsuite:abcd1234",
  "manifest": {
    "d404559f602eab6fd602ac7680dacbfaadd13630335e951f097af3900e9de176b6db28512f2e000b9d04fba5133e8b1c6e8df59db3a8ab9d60be4b97cc9e81db": [ "v1/content/file.txt" ],
    "d716a4188569b68ab1b6dfac178e570114cdf0ea3a1cc0e31486c3e41241bc6a76424e8c37ab26f096fc85ef9886c8cb634187f4fddff645fb099f1ff54c6b8c": [ "v3/content/something" ],
  },
  "type": "https://ocfl.io/1.0/spec/#inventory",
  "versions": {
    "v1": {
      "created": "2018-10-02T12:00:00Z",
      "message": "One file",
      "state": {
        "d404559f602eab6fd602ac7680dacbfaadd13630335e951f097af3900e9de176b6db28512f2e000b9d04fba5133e8b1c6e8df59db3a8ab9d60be4b97cc9e81db": [ "file.txt" ]
      },
      "user": {
        "address": "alice@example.org",
        "name": "Alice"
      }
    },
    "v2": {
      "created": "2018-10-03T12:00:00Z",
      "message": "remove file",
      "state": {},
      "user": {
        "address": "alice@example.org",
        "name": "Alice"
      }
    },
    "v3": {
      "created": "2018-10-04T12:00:00Z",
      "message": "add files",
      "state": {
        "d404559f602eab6fd602ac7680dacbfaadd13630335e951f097af3900e9de176b6db28512f2e000b9d04fba5133e8b1c6e8df59db3a8ab9d60be4b97cc9e81db": [ "renamed_file.txt" ],
        "d716a4188569b68ab1b6dfac178e570114cdf0ea3a1cc0e31486c3e41241bc6a76424e8c37ab26f096fc85ef9886c8cb634187f4fddff645fb099f1ff54c6b8c": [ "something" ],
      },
      "user": {
        "address": "alice@example.org",
        "name": "Alice"
      }
    },
  }
}


class TestOcfl(unittest.TestCase):

    def tearDown(self):
        try:
            shutil.rmtree(os.path.join(ocfl.OCFL_ROOT, '1b5'))
        except FileNotFoundError:
            pass

    def test_object_path(self):
        self.assertEqual(ocfl.object_path('testsuite:abcd1234'), os.path.join(ocfl.OCFL_ROOT, '1b5', '64f', '1ff', 'testsuite%3aabcd1234'))

    def test_datetime_from_string(self):
        self.assertEqual(ocfl.utc_datetime_from_string('2021-03-23T10:20:30Z'), datetime(2021, 3, 23, 10, 20, 30, tzinfo=timezone.utc))
        self.assertEqual(ocfl.utc_datetime_from_string('2021-03-23T10:20:30.000Z'), datetime(2021, 3, 23, 10, 20, 30, tzinfo=timezone.utc))
        self.assertEqual(ocfl.utc_datetime_from_string('2020-11-25T20:30:43.737Z'), datetime(2020, 11, 25, 20, 30, 43, 737000, tzinfo=timezone.utc))
        self.assertEqual(ocfl.utc_datetime_from_string('2020-11-25T20:30:43.73776Z'), datetime(2020, 11, 25, 20, 30, 43, 737760, tzinfo=timezone.utc))
        self.assertEqual(ocfl.utc_datetime_from_string('2021-03-23T10:20:30.522328Z'), datetime(2021, 3, 23, 10, 20, 30, 522328, tzinfo=timezone.utc))
        dt = ocfl.utc_datetime_from_string('2021-03-23T06:20:30.522328-04:00')
        self.assertEqual(dt, datetime(2021, 3, 23, 10, 20, 30, 522328, tzinfo=timezone.utc))
        with self.assertRaises(ocfl.DateTimeError):
            ocfl.utc_datetime_from_string('2021-03-23T06:20:30')

    def test_object(self):
        object_path = os.path.join(ocfl.OCFL_ROOT, '1b5', '64f', '1ff', 'testsuite%3aabcd1234')
        os.makedirs(object_path)
        with open(os.path.join(object_path, 'inventory.json'), 'wb') as f:
            f.write(json.dumps(SIMPLE_INVENTORY).encode('utf8'))
        v1_content_path = os.path.join(object_path, 'v1', 'content')
        v3_content_path = os.path.join(object_path, 'v3', 'content')
        file_txt_path = os.path.join(v1_content_path, 'file.txt')
        something_path = os.path.join(v3_content_path, 'something')
        os.makedirs(v1_content_path)
        os.makedirs(v3_content_path)
        with open(file_txt_path, 'wb') as f:
            f.write(b'1234')
        with open(something_path, 'wb') as f:
            f.write(b'abcdefg')
        o = ocfl.Object('testsuite:abcd1234')
        self.assertEqual(o.get_path_to_file('renamed_file.txt'), file_txt_path)
        with self.assertRaises(FileNotFoundError):
            o.get_path_to_file('file.txt', version='v2')
        self.assertEqual(o.get_path_to_file('file.txt', 'v1'), file_txt_path)

        self.assertEqual(o.head_version, 'v3')
        self.assertEqual(o.created, datetime(2018, 10, 2, 12, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(o.last_modified, datetime(2018, 10, 4, 12, 0, 0, tzinfo=timezone.utc))

        self.assertEqual(sorted(o.filenames), ['renamed_file.txt', 'something'])
        self.assertEqual(sorted(o.all_filenames), ['file.txt', 'renamed_file.txt', 'something'])
