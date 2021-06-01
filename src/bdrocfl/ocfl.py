from datetime import datetime, timezone
import hashlib
import json
import mimetypes
import os
import xml.etree.ElementTree as ET


class ObjectNotFound(RuntimeError):
    pass

class ObjectDeleted(RuntimeError):
    pass

class InventoryError(RuntimeError):
    pass

class DateTimeError(RuntimeError):
    pass


def get_env_variable(var):
    try:
        return os.environ[var]
    except KeyError:
        raise Exception(f'must set "{var}" environment variable')


OCFL_ROOT = get_env_variable('OCFL_ROOT')
RELS_INT_NS = {'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'ns1': 'info:fedora/fedora-system:def/model#'}
DNG_MIMETYPE = 'image/x-adobe-dng'
JS_MIMETYPE = 'application/javascript'
MKV_MIMETYPE = 'video/x-matroska'

mimetypes.add_type(DNG_MIMETYPE, '.dng', strict=False)
mimetypes.add_type(JS_MIMETYPE, '.js', strict=False)
mimetypes.add_type(MKV_MIMETYPE, '.mkv', strict=False)


def get_mimetype_from_filename(filename):
    if filename.endswith('.tei.xml') or filename.endswith('.tei'):
        return 'application/tei+xml'
    if '.' not in filename:
        filename = 'a.%s' % filename
    guessed, _ = mimetypes.guess_type(filename, strict=False)
    if guessed:
        return guessed
    else:
        return 'application/octet-stream'


def get_download_filename_from_rels_int(rels_int_root, pid, filepath):
    if rels_int_root:
        for description in rels_int_root.findall('rdf:Description', RELS_INT_NS):
            if description.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about') == f'info:fedora/{pid}/{filepath}':
                for child in description:
                    if child.tag == '{info:fedora/fedora-system:def/model#}downloadFilename':
                        return os.path.basename(child.text)


def object_path(pid):
    sha256_checksum = hashlib.sha256(pid.encode('utf8')).hexdigest()
    return os.path.join(
            OCFL_ROOT,
            sha256_checksum[0:3],
            sha256_checksum[3:6],
            sha256_checksum[6:9],
            pid.replace(':', '%3a'),
        )


def utc_datetime_from_string(s):
    try:
        dt = datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%f%z')
    except ValueError:
        try:
            dt = datetime.strptime(s, '%Y-%m-%dT%H:%M:%S%z')
        except ValueError:
            raise DateTimeError(f'unrecognized datetime format: {s}')
    return dt.astimezone(tz=timezone.utc)


class Object:

    def __init__(self, pid, fallback_to_version_directory=True):
        self.pid = pid
        self._fallback_to_version_directory = fallback_to_version_directory
        self.object_path = object_path(self.pid)
        if not os.path.exists(self.object_path):
            raise ObjectNotFound()
        self._inventory = self._get_inventory(self.object_path)
        self.head_version = self._inventory['head']
        if not self._inventory['versions'][self.head_version]['state']:
            raise ObjectDeleted()
        self._files_info = None

    def _get_inventory(self, object_path):
        inventory_path = os.path.join(object_path, 'inventory.json')
        try:
            with open(inventory_path, 'rb') as f:
                data = f.read().decode('utf8')
        except FileNotFoundError:
            if self._fallback_to_version_directory:
                version_dirs = []
                with os.scandir(object_path) as it:
                    for entry in it:
                        if entry.is_dir() and entry.name.startswith('v'):
                            version_dirs.append(entry.name)
                version_dirs.sort(key=lambda name: int(name.replace('v', '')), reverse=True)
                inventory_path = os.path.join(object_path, version_dirs[0], 'inventory.json')
                try:
                    with open(inventory_path, 'rb') as f:
                        data = f.read().decode('utf8')
                except FileNotFoundError:
                    raise InventoryError(f'{self.pid} missing root inventory and {version_dirs[0]} inventory')
            else:
                raise InventoryError(f'{self.pid} missing root inventory - not trying version directory')
        return json.loads(data)

    def _get_files_info(self):
        info = {}
        try:
            rels_int_path = self.get_path_to_file('RELS-INT')
            with open(rels_int_path, 'rb') as rels_int_file:
                rels_int_bytes = rels_int_file.read()
            rels_int_root = ET.fromstring(rels_int_bytes)
        except FileNotFoundError:
            rels_int_root = None
        for checksum, filepaths in self._inventory['versions'][self.head_version]['state'].items():
            for filepath in filepaths:
                if filepath not in info:
                    file_info = {
                            'last_modified': utc_datetime_from_string(self._inventory['versions'][self.head_version]['created']),
                            'checksum': checksum,
                            'checksum_type': 'SHA-512',
                            'state': 'A',
                            'size': os.stat(os.path.join(self.object_path, self._inventory['manifest'][checksum][0])).st_size,
                        }
                    download_filename = get_download_filename_from_rels_int(rels_int_root, self.pid, filepath)
                    if not download_filename:
                        download_filename = filepath
                    mimetype = get_mimetype_from_filename(download_filename)
                    file_info['mimetype'] = mimetype
                    file_info['download_filename'] = download_filename
                    info[filepath] = file_info
        #need to backtrack through versions to get/verify the correct last_modified time
        #if a file was present with the same checksum in the previous version, then the last_modified time needs to be updated
        file_handled_mapping = {} #tells us we've already set the correct last_modified time for a filepath, so don't update it again
        for filepath in info.keys():
            file_handled_mapping[filepath] = False
        for version_num in list(reversed(list(self._inventory['versions'].keys())))[1:]: #already handled head version
            for checksum, filepaths in self._inventory['versions'][version_num]['state'].items():
                for filepath in filepaths:
                    if filepath in info:
                        if checksum == info[filepath]['checksum'] and not file_handled_mapping[filepath]:
                            info[filepath]['last_modified'] = utc_datetime_from_string(self._inventory['versions'][version_num]['created'])
                            file_handled_mapping[filepath] = True
        return info

    @property
    def created(self):
        return utc_datetime_from_string(self._inventory['versions']['v1']['created'])

    @property
    def last_modified(self):
        last_version = list(self._inventory['versions'].keys())[-1]
        return utc_datetime_from_string(self._inventory['versions'][self.head_version]['created'])

    def get_path_to_file(self, filename, version=None):
        if not version:
            version = list(self._inventory['versions'].keys())[-1]
        for checksum, files in self._inventory['versions'][version]['state'].items():
            for f in files:
                if f == filename:
                    return os.path.join(self.object_path, self._inventory['manifest'][checksum][0])
        raise FileNotFoundError(f'no {filename} file in version {version}')

    @property
    def filenames(self):
        #grab these from inventory.json, instead of self._files_info, so we don't require _get_files_info() to be run
        names = set()
        for checksum, files in self._inventory['versions'][self.head_version]['state'].items():
            for f in files:
                names.add(f)
        return list(names)

    @property
    def all_filenames(self):
        filenames = set()
        reversed_version_nums = list(reversed(list(self._inventory['versions'].keys()))) #eg. 'v3', 'v2', 'v1'
        for v in reversed_version_nums:
            for checksum, filepaths in self._inventory['versions'][v]['state'].items():
                for f in filepaths:
                    filenames.add(f)
        return filenames

    def get_files_info(self):
        #returns file information for *active* files
        if not self._files_info:
            self._files_info = self._get_files_info()
        return self._files_info
