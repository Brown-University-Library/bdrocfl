import copy
from datetime import datetime, timezone
import json
import os
import shutil
import unittest
from bdrocfl import ocfl


SIMPLE_INVENTORY = {
  "digestAlgorithm": "sha512",
  "head": "v4",
  "id": "testsuite:abcd1234",
  "manifest": {
    "d404559f602eab6fd602ac7680dacbfaadd13630335e951f097af3900e9de176b6db28512f2e000b9d04fba5133e8b1c6e8df59db3a8ab9d60be4b97cc9e81db": [ "v1/content/file.txt" ],
    "d716a4188569b68ab1b6dfac178e570114cdf0ea3a1cc0e31486c3e41241bc6a76424e8c37ab26f096fc85ef9886c8cb634187f4fddff645fb099f1ff54c6b8c": [ "v3/content/something" ],
    "e9a02f16c5514f23a49eec017e35e08e5c3e7414b33456f17502232c6a6e7a9196f831ab0764954fcb8df398c494d5091c64356dfe42e831b6949eab2449371e": [ "v3/content/RELS-INT" ],
  },
  "type": "https://ocfl.io/1.0/spec/#inventory",
  "versions": {
    "v1": {
      "created": "2018-10-02T12:00:00Z",
      "message": "One file",
      "state": {
        "d404559f602eab6fd602ac7680dacbfaadd13630335e951f097af3900e9de176b6db28512f2e000b9d04fba5133e8b1c6e8df59db3a8ab9d60be4b97cc9e81db": [ "file.txt" ],
        "d716a4188569b68ab1b6dfac178e570114cdf0ea3a1cc0e31486c3e41241bc6a76424e8c37ab26f096fc85ef9886c8cb634187f4fddff645fb099f1ff54c6b8c": [ "something" ],
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
        "e9a02f16c5514f23a49eec017e35e08e5c3e7414b33456f17502232c6a6e7a9196f831ab0764954fcb8df398c494d5091c64356dfe42e831b6949eab2449371e": [ "RELS-INT" ],
      },
      "user": {
        "address": "alice@example.org",
        "name": "Alice"
      }
    },
    "v4": {
      "created": "2018-10-05T12:00:00Z",
      "message": "add another file (duplicate)",
      "state": {
        "d404559f602eab6fd602ac7680dacbfaadd13630335e951f097af3900e9de176b6db28512f2e000b9d04fba5133e8b1c6e8df59db3a8ab9d60be4b97cc9e81db": [ "renamed_file.txt" ],
        "d716a4188569b68ab1b6dfac178e570114cdf0ea3a1cc0e31486c3e41241bc6a76424e8c37ab26f096fc85ef9886c8cb634187f4fddff645fb099f1ff54c6b8c": [ "something", "something else" ],
        "e9a02f16c5514f23a49eec017e35e08e5c3e7414b33456f17502232c6a6e7a9196f831ab0764954fcb8df398c494d5091c64356dfe42e831b6949eab2449371e": [ "RELS-INT" ],
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

    def test_object_not_found(self):
        with self.assertRaises(ocfl.ObjectNotFound):
            ocfl.Object('testsuite:abcd1234')

    def test_object_deleted(self):
        object_path = os.path.join(ocfl.OCFL_ROOT, '1b5', '64f', '1ff', 'testsuite%3aabcd1234')
        os.makedirs(object_path)
        inventory = copy.deepcopy(SIMPLE_INVENTORY)
        inventory['head'] = 'v4'
        inventory['versions']['v4'] = {
            "created": "2018-10-05T12:00:00Z",
            "message": "delete object",
            "state": {},
            "user": {
              "address": "alice@example.org",
              "name": "Alice"
            }
        }
        with open(os.path.join(object_path, 'inventory.json'), 'wb') as f:
            f.write(json.dumps(inventory).encode('utf8'))
        with self.assertRaises(ocfl.ObjectDeleted):
            ocfl.Object('testsuite:abcd1234')

    def test_object(self):
        object_path = os.path.join(ocfl.OCFL_ROOT, '1b5', '64f', '1ff', 'testsuite%3aabcd1234')
        os.makedirs(object_path)
        with open(os.path.join(object_path, 'inventory.json'), 'wb') as f:
            f.write(json.dumps(SIMPLE_INVENTORY).encode('utf8'))
        v1_content_path = os.path.join(object_path, 'v1', 'content')
        v3_content_path = os.path.join(object_path, 'v3', 'content')
        file_txt_path = os.path.join(v1_content_path, 'file.txt')
        something_path = os.path.join(v3_content_path, 'something')
        rels_int_path = os.path.join(v3_content_path, 'RELS-INT')
        os.makedirs(v1_content_path)
        os.makedirs(v3_content_path)
        rels_int = '''<rdf:RDF xmlns:ns1="info:fedora/fedora-system:def/model#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about="info:fedora/testsuite:abcd1234/something">
    <ns1:downloadFilename>some image.jpg</ns1:downloadFilename>
    <rdf:type rdf:resource="http://pcdm.org/use#OriginalFile"/>
  </rdf:Description>
</rdf:RDF>'''

        with open(file_txt_path, 'wb') as f:
            f.write(b'1234')
        with open(something_path, 'wb') as f:
            f.write(b'abcdefg')
        with open(rels_int_path, 'wb') as f:
            f.write(rels_int.encode('utf8'))
        o = ocfl.Object('testsuite:abcd1234')
        self.assertEqual(o.get_path_to_file('renamed_file.txt'), file_txt_path)
        with self.assertRaises(FileNotFoundError):
            o.get_path_to_file('file.txt', version='v2')
        self.assertEqual(o.get_path_to_file('file.txt', 'v1'), file_txt_path)

        self.assertEqual(o.head_version, 'v4')
        self.assertEqual(o.created, datetime(2018, 10, 2, 12, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(o.last_modified, datetime(2018, 10, 5, 12, 0, 0, tzinfo=timezone.utc))

        self.assertEqual(sorted(o.filenames), ['RELS-INT', 'renamed_file.txt', 'something', 'something else'])
        self.assertEqual(sorted(o.all_filenames), ['RELS-INT', 'file.txt', 'renamed_file.txt', 'something', 'something else'])
        self.maxDiff = None
        self.assertEqual(o.get_files_info(), {
            'RELS-INT': {
                'state': 'A',
                'size': 347,
                'checksum': 'e9a02f16c5514f23a49eec017e35e08e5c3e7414b33456f17502232c6a6e7a9196f831ab0764954fcb8df398c494d5091c64356dfe42e831b6949eab2449371e',
                'checksum_type': 'SHA-512',
                'mimetype': 'application/octet-stream',
                'download_filename': 'RELS-INT',
                'last_modified': datetime(2018, 10, 4, 12, 0, 0, tzinfo=timezone.utc),
            },
            'renamed_file.txt': {
                'state': 'A',
                'size': 4,
                'checksum': 'd404559f602eab6fd602ac7680dacbfaadd13630335e951f097af3900e9de176b6db28512f2e000b9d04fba5133e8b1c6e8df59db3a8ab9d60be4b97cc9e81db',
                'checksum_type': 'SHA-512',
                'mimetype': 'text/plain',
                'download_filename': 'renamed_file.txt',
                'last_modified': datetime(2018, 10, 4, 12, 0, 0, tzinfo=timezone.utc),
            },
            'something': {
                'state': 'A',
                'size': 7,
                'checksum': 'd716a4188569b68ab1b6dfac178e570114cdf0ea3a1cc0e31486c3e41241bc6a76424e8c37ab26f096fc85ef9886c8cb634187f4fddff645fb099f1ff54c6b8c',
                'checksum_type': 'SHA-512',
                'mimetype': 'image/jpeg',
                'download_filename': 'some image.jpg',
                'last_modified': datetime(2018, 10, 4, 12, 0, 0, tzinfo=timezone.utc),
            },
            'something else': {
                'state': 'A',
                'size': 7,
                'checksum': 'd716a4188569b68ab1b6dfac178e570114cdf0ea3a1cc0e31486c3e41241bc6a76424e8c37ab26f096fc85ef9886c8cb634187f4fddff645fb099f1ff54c6b8c',
                'checksum_type': 'SHA-512',
                'mimetype': 'application/octet-stream',
                'download_filename': 'something else',
                'last_modified': datetime(2018, 10, 5, 12, 0, 0, tzinfo=timezone.utc),
            },
        })

    def test_root_inventory_error(self):
        object_path = os.path.join(ocfl.OCFL_ROOT, '1b5', '64f', '1ff', 'testsuite%3aabcd1234')
        os.makedirs(object_path)
        v1_content_path = os.path.join(object_path, 'v1', 'content')
        v3_content_path = os.path.join(object_path, 'v3', 'content')
        v4_content_path = os.path.join(object_path, 'v4', 'content')
        file_txt_path = os.path.join(v1_content_path, 'file.txt')
        something_path = os.path.join(v3_content_path, 'something')
        os.makedirs(v1_content_path)
        os.makedirs(v3_content_path)
        os.makedirs(v4_content_path)
        with open(file_txt_path, 'wb') as f:
            f.write(b'1234')
        with open(something_path, 'wb') as f:
            f.write(b'abcdefg')

        #no version inventory to fallback to
        with self.assertRaises(ocfl.InventoryError):
            ocfl.Object('testsuite:abcd1234')

        #now verify that version inventory fallback works
        v4_inventory_path = os.path.join(object_path, 'v4', 'inventory.json')
        with open(v4_inventory_path, 'wb') as f:
            f.write(json.dumps(SIMPLE_INVENTORY).encode('utf8'))
        o = ocfl.Object('testsuite:abcd1234')
        self.assertEqual(o.head_version, 'v4')
        self.assertEqual(sorted(o.filenames), ['RELS-INT', 'renamed_file.txt', 'something', 'something else'])

        #check that we can turn off the feature to fall back to the version directory
        with self.assertRaises(ocfl.InventoryError):
            ocfl.Object('testsuite:abcd1234', fallback_to_version_directory=False)
