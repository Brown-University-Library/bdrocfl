import os
import hashlib


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
