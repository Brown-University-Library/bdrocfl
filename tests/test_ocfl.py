import copy
from datetime import datetime, timezone
import json
import os
import shutil
import timeit
import unittest
from bdrocfl import ocfl, test_utils


OCFL_ROOT = os.environ['OCFL_ROOT']


SIMPLE_INVENTORY = {
  "digestAlgorithm": "sha512",
  "head": "v5",
  "id": "testsuite:abcd1234",
  "manifest": {
    "d404559f602eab6fd602ac7680dacbfaadd13630335e951f097af3900e9de176b6db28512f2e000b9d04fba5133e8b1c6e8df59db3a8ab9d60be4b97cc9e81db": [ "v1/content/file.txt" ],
    "d716a4188569b68ab1b6dfac178e570114cdf0ea3a1cc0e31486c3e41241bc6a76424e8c37ab26f096fc85ef9886c8cb634187f4fddff645fb099f1ff54c6b8c": [ "v3/content/something" ],
    "e9a02f16c5514f23a49eec017e35e08e5c3e7414b33456f17502232c6a6e7a9196f831ab0764954fcb8df398c494d5091c64356dfe42e831b6949eab2449371e": [ "v3/content/RELS-INT" ],
  },
  "type": "https://ocfl.io/1.0/spec/#inventory",
  "versions": {
    "v1": {
      "created": "2018-10-01T12:00:00Z",
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
    "v4": {
      "created": "2018-10-04T12:00:00Z",
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
    "v5": {
      "created": "2018-10-05T12:00:00Z",
      "message": "and add another file",
      "state": {
        "d404559f602eab6fd602ac7680dacbfaadd13630335e951f097af3900e9de176b6db28512f2e000b9d04fba5133e8b1c6e8df59db3a8ab9d60be4b97cc9e81db": [ "renamed_file.txt" ],
        "d716a4188569b68ab1b6dfac178e570114cdf0ea3a1cc0e31486c3e41241bc6a76424e8c37ab26f096fc85ef9886c8cb634187f4fddff645fb099f1ff54c6b8c": [ "something", "something else" ],
        "e9a02f16c5514f23a49eec017e35e08e5c3e7414b33456f17502232c6a6e7a9196f831ab0764954fcb8df398c494d5091c64356dfe42e831b6949eab2449371e": [ "RELS-INT", "RELS-INT2" ],
      },
      "user": {
        "address": "alice@example.org",
        "name": "Alice"
      }
    },
    "v2": {
      "created": "2018-10-02T12:00:00Z",
      "message": "remove all files",
      "state": {},
      "user": {
        "address": "alice@example.org",
        "name": "Alice"
      }
    },
    "v3": {
      "created": "2018-10-03T12:00:00Z",
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
  }
}


class TestOcfl(unittest.TestCase):

    def setUp(self):
        try:
            shutil.rmtree(os.path.join(OCFL_ROOT, '1b5'))
        except FileNotFoundError:
            pass

    def test_object_path(self):
        self.assertEqual(ocfl.object_path('/tmp/ocfl_root', 'testsuite:abcd1234'), os.path.join('/tmp', 'ocfl_root', '1b5', '64f', '1ff', 'testsuite%3aabcd1234'))

    def test_get_mimetype_from_filename(self):
        self.assertEqual(ocfl.get_mimetype_from_filename('RELS-INT'), 'text/xml')
        self.assertEqual(ocfl.get_mimetype_from_filename('RELS-EXT'), 'text/xml')
        self.assertEqual(ocfl.get_mimetype_from_filename('MODS'), 'text/xml')
        self.assertEqual(ocfl.get_mimetype_from_filename('DWC'), 'text/xml')
        self.assertEqual(ocfl.get_mimetype_from_filename('TEI'), 'application/tei+xml')
        self.assertEqual(ocfl.get_mimetype_from_filename('DIGITAL-NEGATIVE'), ocfl.DNG_MIMETYPE)
        self.assertEqual(ocfl.get_mimetype_from_filename('image.dng'), ocfl.DNG_MIMETYPE)
        self.assertEqual(ocfl.get_mimetype_from_filename('image.DNG'), ocfl.DNG_MIMETYPE)
        self.assertEqual(ocfl.get_mimetype_from_filename('file.TEI'), 'application/tei+xml')

    def test_datetime_from_string(self):
        self.maxDiff = None
        dt = ocfl.utc_datetime_from_string('2021-03-23T06:20:30.522328-04:00')
        self.assertEqual(dt, datetime(2021, 3, 23, 10, 20, 30, 522328, tzinfo=timezone.utc))
        dt = ocfl.utc_datetime_from_string('2021-03-23T14:20:30.522328+04:00')
        self.assertEqual(dt, datetime(2021, 3, 23, 10, 20, 30, 522328, tzinfo=timezone.utc))
        self.assertEqual(ocfl.utc_datetime_from_string('2021-03-23T10:20:30Z'), datetime(2021, 3, 23, 10, 20, 30, tzinfo=timezone.utc))
        self.assertEqual(ocfl.utc_datetime_from_string('2021-03-23T10:20:30.000Z'), datetime(2021, 3, 23, 10, 20, 30, tzinfo=timezone.utc))
        self.assertEqual(ocfl.utc_datetime_from_string('2020-11-25T20:30:43.7Z'), datetime(2020, 11, 25, 20, 30, 43, 700000, tzinfo=timezone.utc))
        self.assertEqual(ocfl.utc_datetime_from_string('2020-11-25T22:30:43.7+02:00'), datetime(2020, 11, 25, 20, 30, 43, 700000, tzinfo=timezone.utc))
        self.assertEqual(ocfl.utc_datetime_from_string('2020-11-25T22:30:43+02:00'), datetime(2020, 11, 25, 20, 30, 43, 0, tzinfo=timezone.utc))
        self.assertEqual(ocfl.utc_datetime_from_string('2020-11-25T18:30:43-02:00'), datetime(2020, 11, 25, 20, 30, 43, 0, tzinfo=timezone.utc))
        self.assertEqual(ocfl.utc_datetime_from_string('2020-11-25T20:30:43.73Z'), datetime(2020, 11, 25, 20, 30, 43, 730000, tzinfo=timezone.utc))
        self.assertEqual(ocfl.utc_datetime_from_string('2020-11-25T20:30:43.737Z'), datetime(2020, 11, 25, 20, 30, 43, 737000, tzinfo=timezone.utc)) #common in fedora history
        self.assertEqual(ocfl.utc_datetime_from_string('2020-11-25T20:30:43.73776Z'), datetime(2020, 11, 25, 20, 30, 43, 737760, tzinfo=timezone.utc)) #in ocfl objs, but maybe more rare than next one
        self.assertEqual(ocfl.utc_datetime_from_string('2021-03-23T10:20:30.522328Z'), datetime(2021, 3, 23, 10, 20, 30, 522328, tzinfo=timezone.utc)) #common in new ocfl objs
        with self.assertRaises(ocfl.DateTimeError):
            ocfl.utc_datetime_from_string('2021-03-23T06:20:30')
        #now time the functions
        print('datetime parsing speeds:')
        for date_string in ['2021-03-23T06:20:30.522328-04:00', '2021-03-23T06:20:30.52232-04:00', '2020-11-25T20:30:43.737Z', '2020-11-25T20:30:43.73776Z', '2020-11-25T20:30:43.737760Z']:
            print(date_string)
            speed = timeit.timeit(f'ocfl.utc_datetime_from_string("{date_string}")', number=10000, setup='from bdrocfl import ocfl')
            print(f'  utc_datetime_from_string: {speed}')

    def test_reversed_version_numbers(self):
        self.assertEqual(ocfl.Object.reversed_version_numbers('v10'), ['v10', 'v9', 'v8', 'v7', 'v6', 'v5', 'v4', 'v3', 'v2', 'v1'])

    def test_object_not_found(self):
        with self.assertRaises(ocfl.ObjectNotFound):
            ocfl.Object(OCFL_ROOT, 'testsuite:abcd1234')

    def test_object_deleted(self):
        test_utils.create_deleted_object(OCFL_ROOT, pid='testsuite:abcd1234')
        with self.assertRaises(ocfl.ObjectDeleted):
            ocfl.Object(OCFL_ROOT, 'testsuite:abcd1234')
        obj = ocfl.Object(OCFL_ROOT, 'testsuite:abcd1234', deleted_ok=True)
        self.assertEqual(obj.pid, 'testsuite:abcd1234')

    def test_object(self):
        object_path = os.path.join(OCFL_ROOT, '1b5', '64f', '1ff', 'testsuite%3aabcd1234')
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
        o = ocfl.Object(OCFL_ROOT, 'testsuite:abcd1234')
        self.assertEqual(o.get_path_to_file('renamed_file.txt'), file_txt_path)
        with self.assertRaises(FileNotFoundError):
            o.get_path_to_file('file.txt', version='v2')
        self.assertEqual(o.get_path_to_file('file.txt', 'v1'), file_txt_path)

        self.assertEqual(o.head_version, 'v5')
        self.assertEqual(o.created, datetime(2018, 10, 1, 12, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(o.last_modified, datetime(2018, 10, 5, 12, 0, 0, tzinfo=timezone.utc))

        self.assertEqual(sorted(o.filenames), ['RELS-INT', 'RELS-INT2', 'renamed_file.txt', 'something', 'something else'])
        self.assertEqual(sorted(o.all_filenames), ['RELS-INT', 'RELS-INT2', 'file.txt', 'renamed_file.txt', 'something', 'something else'])
        self.maxDiff = None
        self.assertEqual(o.get_files_info(), {'RELS-INT': {}, 'RELS-INT2': {}, 'renamed_file.txt': {}, 'something': {}, 'something else': {}})
        self.assertEqual(o.get_files_info(include_deleted=True), {'RELS-INT': {}, 'RELS-INT2': {}, 'renamed_file.txt': {}, 'something': {}, 'something else': {}, 'file.txt': {}})
        self.assertEqual(o.get_files_info(include_deleted=True, fields=['state']), {
            'RELS-INT': {'state': 'A'},
            'RELS-INT2': {'state': 'A'},
            'renamed_file.txt': {'state': 'A'},
            'something': {'state': 'A'},
            'something else': {'state': 'A'},
            'file.txt': {'state': 'D'},
        })
        self.assertEqual(o.get_files_info(include_deleted=True, fields=['mimetype']), {
            'RELS-INT': {'mimetype': 'text/xml'},
            'RELS-INT2': {'mimetype': 'application/octet-stream'},
            'renamed_file.txt': {'mimetype': 'text/plain'},
            'something': {'mimetype': 'image/jpeg'},
            'something else': {'mimetype': 'application/octet-stream'},
            'file.txt': {'mimetype': 'text/plain'},
        })
        self.assertEqual(o.get_files_info(fields=['state', 'size', 'checksum', 'checksumType', 'mimetype', 'downloadFilename', 'lastModified']), {
            'RELS-INT': {
                'state': 'A',
                'size': 347,
                'checksum': 'e9a02f16c5514f23a49eec017e35e08e5c3e7414b33456f17502232c6a6e7a9196f831ab0764954fcb8df398c494d5091c64356dfe42e831b6949eab2449371e',
                'checksumType': 'SHA-512',
                'mimetype': 'text/xml',
                'downloadFilename': 'RELS-INT',
                'lastModified': datetime(2018, 10, 3, 12, 0, 0, tzinfo=timezone.utc),
            },
            'RELS-INT2': {
                'state': 'A',
                'size': 347,
                'checksum': 'e9a02f16c5514f23a49eec017e35e08e5c3e7414b33456f17502232c6a6e7a9196f831ab0764954fcb8df398c494d5091c64356dfe42e831b6949eab2449371e',
                'checksumType': 'SHA-512',
                'mimetype': 'application/octet-stream',
                'downloadFilename': 'RELS-INT2',
                'lastModified': datetime(2018, 10, 5, 12, 0, 0, tzinfo=timezone.utc),
            },
            'renamed_file.txt': {
                'state': 'A',
                'size': 4,
                'checksum': 'd404559f602eab6fd602ac7680dacbfaadd13630335e951f097af3900e9de176b6db28512f2e000b9d04fba5133e8b1c6e8df59db3a8ab9d60be4b97cc9e81db',
                'checksumType': 'SHA-512',
                'mimetype': 'text/plain',
                'downloadFilename': 'renamed_file.txt',
                'lastModified': datetime(2018, 10, 3, 12, 0, 0, tzinfo=timezone.utc),
            },
            'something': {
                'state': 'A',
                'size': 7,
                'checksum': 'd716a4188569b68ab1b6dfac178e570114cdf0ea3a1cc0e31486c3e41241bc6a76424e8c37ab26f096fc85ef9886c8cb634187f4fddff645fb099f1ff54c6b8c',
                'checksumType': 'SHA-512',
                'mimetype': 'image/jpeg',
                'downloadFilename': 'some image.jpg',
                'lastModified': datetime(2018, 10, 3, 12, 0, 0, tzinfo=timezone.utc),
            },
            'something else': {
                'state': 'A',
                'size': 7,
                'checksum': 'd716a4188569b68ab1b6dfac178e570114cdf0ea3a1cc0e31486c3e41241bc6a76424e8c37ab26f096fc85ef9886c8cb634187f4fddff645fb099f1ff54c6b8c',
                'checksumType': 'SHA-512',
                'mimetype': 'application/octet-stream',
                'downloadFilename': 'something else',
                'lastModified': datetime(2018, 10, 4, 12, 0, 0, tzinfo=timezone.utc),
            },
        })

    def test_root_inventory_error(self):
        object_path = os.path.join(OCFL_ROOT, '1b5', '64f', '1ff', 'testsuite%3aabcd1234')
        os.makedirs(object_path)
        v1_content_path = os.path.join(object_path, 'v1', 'content')
        v3_content_path = os.path.join(object_path, 'v3', 'content')
        v4_content_path = os.path.join(object_path, 'v4', 'content')
        v5_content_path = os.path.join(object_path, 'v5', 'content')
        file_txt_path = os.path.join(v1_content_path, 'file.txt')
        something_path = os.path.join(v3_content_path, 'something')
        os.makedirs(v1_content_path)
        os.makedirs(v3_content_path)
        os.makedirs(v4_content_path)
        os.makedirs(v5_content_path)
        with open(file_txt_path, 'wb') as f:
            f.write(b'1234')
        with open(something_path, 'wb') as f:
            f.write(b'abcdefg')

        #no version inventory to fallback to
        with self.assertRaises(ocfl.InventoryError):
            ocfl.Object(OCFL_ROOT, 'testsuite:abcd1234')

        #now verify that version inventory fallback works
        inventory_path = os.path.join(object_path, 'v5', 'inventory.json')
        with open(inventory_path, 'wb') as f:
            f.write(json.dumps(SIMPLE_INVENTORY).encode('utf8'))
        o = ocfl.Object(OCFL_ROOT, 'testsuite:abcd1234')
        self.assertEqual(o.head_version, 'v5')
        self.assertEqual(sorted(o.filenames), ['RELS-INT', 'RELS-INT2', 'renamed_file.txt', 'something', 'something else'])

        #check that we can turn off the feature to fall back to the version directory
        with self.assertRaises(ocfl.InventoryError):
            ocfl.Object(OCFL_ROOT, 'testsuite:abcd1234', fallback_to_version_directory=False)


class TestTestUtils(unittest.TestCase):

    def setUp(self):
        self.pid = 'testsuite:abcd1234'
        try:
            shutil.rmtree(os.path.join(OCFL_ROOT, '1b5'))
        except FileNotFoundError:
            pass

    def test_create_object(self):
        test_utils.create_object(OCFL_ROOT, self.pid, files=[('file1', b'abcd')])
        object_root = os.path.join(OCFL_ROOT, '1b5', '64f', '1ff', 'testsuite%3aabcd1234')
        inventory_path = os.path.join(object_root, 'inventory.json')
        with open(inventory_path, 'rb') as f:
            inventory_data = f.read().decode('utf8')
        inventory = json.loads(inventory_data)
        self.assertEqual(inventory['id'], self.pid)
        self.assertEqual(inventory['versions']['v1']['state'], {'d8022f2060ad6efd297ab73dcc5355c9b214054b0d1776a136a669d26a7d3b14f73aa0d0ebff19ee333368f0164b6419a96da49e3e481753e7e96b716bdccb6f': ['file1']})
        file1_path = os.path.join(object_root, 'v1', 'content', 'file1')
        with open(file1_path, 'rb') as f:
            self.assertEqual(f.read(), b'abcd')

    def test_create_deleted_object(self):
        test_utils.create_deleted_object(storage_root=OCFL_ROOT, pid=self.pid)
        object_root = os.path.join(OCFL_ROOT, '1b5', '64f', '1ff', 'testsuite%3aabcd1234')
        inventory_path = os.path.join(object_root, 'inventory.json')
        with open(inventory_path, 'rb') as f:
            inventory_data = f.read().decode('utf8')
        inventory = json.loads(inventory_data)
        self.assertEqual(inventory['versions'][inventory['head']]['state'], {})
