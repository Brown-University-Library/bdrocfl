from datetime import datetime, timezone, timedelta
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


def _micro_seconds_from_micro_str(micro_str):
    micro_str_len = len(micro_str)
    if micro_str_len == 6:
        micro_seconds = int(micro_str)
    elif micro_str_len == 5:
        micro_seconds = int(micro_str) * 10
    elif micro_str_len == 4:
        micro_seconds = int(micro_str) * 100
    elif micro_str_len == 3:
        micro_seconds = int(micro_str) * 1000
    elif micro_str_len == 2:
        micro_seconds = int(micro_str) * 10000
    elif micro_str_len == 1:
        micro_seconds = int(micro_str) * 100000
    else:
        raise DateTimeError(f'invalid microseconds: {micro_str}')
    return micro_seconds


def utc_datetime_from_string(date_string):
    try:
        #fromisoformat is very fast - try this first
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        if not dt.tzinfo:
            raise DateTimeError(f'datetime must have timezone info: {date_string}')
        return dt
    except ValueError:
        #if fromisoformat failed, fall back to this
        try:
            remaining_date_string = date_string[19:]
            year = int(date_string[0:4])
            month = int(date_string[5:7])
            day = int(date_string[8:10])
            hours = int(date_string[11:13])
            minutes = int(date_string[14:16])
            seconds = int(date_string[17:19])
            micro_seconds = 0
            tzinfo = None
            if remaining_date_string[0] == '.': #we have microseconds
                if remaining_date_string[-1] == 'Z':
                    tzinfo = timezone.utc
                    micro_str = remaining_date_string[1:-1]
                    micro_seconds = _micro_seconds_from_micro_str(micro_str)
                    return datetime(year, month, day, hours, minutes, seconds, micro_seconds, tzinfo)
                elif '+' in remaining_date_string:
                    micro_str, tz_str = remaining_date_string.split('+')
                    micro_str = micro_str[1:]
                    micro_seconds = _micro_seconds_from_micro_str(micro_str)
                    tz_hours, tz_minutes = [int(i) for i in tz_str.split(':')]
                    tzinfo = timezone(timedelta(hours=tz_hours, minutes=tz_minutes))
                elif '-' in remaining_date_string:
                    micro_str, tz_str = remaining_date_string.split('-')
                    micro_str = micro_str[1:]
                    micro_seconds = _micro_seconds_from_micro_str(micro_str)
                    tz_hours, tz_minutes = [int(i) for i in tz_str.split(':')]
                    tzinfo = timezone(timedelta(hours=tz_hours, minutes=tz_minutes) * -1)
                else:
                    raise DateTimeError(f'error parsing {date_string}')
            else: #no microseconds
                if remaining_date_string == 'Z':
                    tzinfo = timezone.utc
                elif remaining_date_string.startswith('+'):
                    tz_str = remaining_date_string[1:]
                    tz_hours, tz_minutes = [int(i) for i in tz_str.split(':')]
                    tzinfo = timezone(timedelta(hours=tz_hours, minutes=tz_minutes))
                elif remaining_date_string.startswith('-'):
                    tz_str = remaining_date_string[1:]
                    tz_hours, tz_minutes = [int(i) for i in tz_str.split(':')]
                    tzinfo = timezone(timedelta(hours=tz_hours, minutes=tz_minutes) * -1)
                else:
                    raise DateTimeError(f'error parsing {date_string}')
            dt = datetime(year, month, day, hours, minutes, seconds, micro_seconds, tzinfo)
            if not dt.tzinfo:
                raise DateTimeError(f'datetime must have timezone info: {date_string}')
            if dt.tzinfo == timezone.utc:
                return dt
            else:
                return dt.astimezone(timezone.utc)
        except DateTimeError:
            raise
        except Exception:
            raise DateTimeError(f'error parsing {datestring}')


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

    @staticmethod
    def reversed_version_numbers(head_version):
        return [f'v{i}' for i in range(int(head_version.replace('v', '')), 0, -1)]

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
        file_handled_mapping = {} #tells us not to update the last_modified time anymore as we keep going back through version history
        for filepath in info.keys():
            file_handled_mapping[filepath] = False
        for version_num in Object.reversed_version_numbers(self.head_version)[1:]: #already handled head version
            files_in_this_version = set()
            for checksum, filepaths in self._inventory['versions'][version_num]['state'].items():
                for filepath in filepaths:
                    if filepath in info:
                        files_in_this_version.add(filepath)
                        if checksum == info[filepath]['checksum'] and not file_handled_mapping[filepath]:
                            info[filepath]['last_modified'] = utc_datetime_from_string(self._inventory['versions'][version_num]['created'])
            #if there are any files in the head version, that aren't in this version, mark that we shouldn't update their time anymore
            for filepath in file_handled_mapping:
                if filepath not in files_in_this_version:
                    file_handled_mapping[filepath] = True
        return info

    @property
    def created(self):
        return utc_datetime_from_string(self._inventory['versions']['v1']['created'])

    @property
    def last_modified(self):
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
        for v in Object.reversed_version_numbers(self.head_version):
            for checksum, filepaths in self._inventory['versions'][v]['state'].items():
                for f in filepaths:
                    filenames.add(f)
        return filenames

    def get_files_info(self):
        #returns file information for *active* files
        if not self._files_info:
            self._files_info = self._get_files_info()
        return self._files_info
