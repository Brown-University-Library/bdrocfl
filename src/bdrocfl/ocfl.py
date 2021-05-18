from datetime import datetime, timezone
import json
import os
import hashlib


class DateTimeError(RuntimeError):
    pass


def get_env_variable(var):
    try:
        return os.environ[var]
    except KeyError:
        raise Exception(f'must set "{var}" environment variable')


OCFL_ROOT = get_env_variable('OCFL_ROOT')


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

    def __init__(self, pid):
        self.pid = pid
        self._object_path = object_path(self.pid)
        self._inventory = self._get_inventory(self._object_path)
        self._files = None

    def _get_inventory(self, object_path):
        inventory_path = os.path.join(object_path, 'inventory.json')
        with open(inventory_path, 'rb') as f:
            data = f.read().decode('utf8')
        return json.loads(data)

    def _get_files_info(self):
        info = {}
        for checksum, filepaths in self._inventory['versions'][self.head_version]['state'].items():
            for f in filepaths:
                if f not in info:
                    info[f] = {'state': 'A'}
        reversed_version_nums = list(reversed(list(self._inventory['versions'].keys()))) #eg. 'v3', 'v2', 'v1'
        for v in reversed_version_nums[1:]:
            for checksum, filepaths in self._inventory['versions'][v]['state'].items():
                for f in filepaths:
                    if f not in info:
                        info[f] = {'state': 'D'}
        return info

    @property
    def _files_info(self):
        if not self._files:
            self._files = self._get_files_info()
        return self._files

    @property
    def head_version(self):
        return self._inventory['head']

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
                    return os.path.join(self._object_path, self._inventory['manifest'][checksum][0])
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
        return [f for f in self._files_info.keys()]
