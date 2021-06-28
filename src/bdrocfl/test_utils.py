'''Tools for testing OCFL repos/objects'''
import hashlib
import json
import os
from . import ocfl


def get_base_inventory(pid):
    return {
            'digestAlgorithm': 'sha512',
            'id': pid,
            'type': 'https://ocfl.io/1.0/spec/#inventory',
            'manifest': {},
            'versions': {},
        }


def get_base_version(created='2018-10-01T12:24:59.123456Z', message='', user_name='Alice', user_address='alice@example.org'):
    return {
            'created': created,
            'message': message,
            'user': {'address': user_address, 'name': user_name},
            'state': {},
        }


def write_inventory_files(object_root, inventory):
    version_root = os.path.join(object_root, inventory['head'])
    if not os.path.exists(version_root):
        os.makedirs(version_root, exist_ok=True)
    inventory_path = os.path.join(object_root, 'inventory.json')
    version_inventory_path = os.path.join(version_root, 'inventory.json')
    inventory_hash_path = os.path.join(object_root, 'inventory.json.sha512')
    version_inventory_hash_path = os.path.join(version_root, 'inventory.json.sha512')
    with open(inventory_path, 'wb') as f:
        f.write(json.dumps(inventory).encode('utf8'))
    with open(version_inventory_path, 'wb') as f:
        f.write(json.dumps(inventory).encode('utf8'))
    inventory_hash = hashlib.sha512(json.dumps(inventory).encode('utf8')).hexdigest()
    inventory_hash_file_content = f'{inventory_hash}\tinventory.json'.encode('utf8')
    with open(inventory_hash_path, 'wb') as f:
        f.write(inventory_hash_file_content)
    with open(version_inventory_hash_path, 'wb') as f:
        f.write(inventory_hash_file_content)


def add_version_to_inventory(inventory, version_num, version, files):
    for file_name, file_content in files:
        file_path = os.path.join(version_num, 'content', file_name)
        file_hash = hashlib.sha512(file_content).hexdigest()
        if file_hash in inventory['manifest']:
            inventory['manifest'][file_hash].append(file_path)
        else:
            inventory['manifest'][file_hash] = [file_path]
        if file_hash in version['state']:
            version['state'][file_hash].append(file_name)
        else:
            version['state'][file_hash] = [file_name]
    inventory['versions'][version_num] = version
    inventory['head'] = version_num


def write_content_files(object_root, version_num, files):
    content_dir = os.path.join(object_root, version_num, 'content')
    if not os.path.exists(content_dir):
        os.makedirs(content_dir, exist_ok=True)
    for file_name, file_content in files:
        file_path = os.path.join(version_num, 'content', file_name)
        with open(os.path.join(object_root, file_path), 'wb') as f:
            f.write(file_content)


def create_object(storage_root, pid, files=(('file1', b'abcd'),)):
    object_root = ocfl.object_path(storage_root, pid)
    inventory = get_base_inventory(pid)
    v1_version = get_base_version()
    add_version_to_inventory(inventory, 'v1', v1_version, files)
    write_inventory_files(object_root, inventory)
    write_content_files(object_root, 'v1', files)


def create_deleted_object(storage_root, pid, files=(('file1', b'abcd'),)):
    object_root = ocfl.object_path(storage_root, pid)
    inventory = get_base_inventory(pid)
    v1_version = get_base_version()
    add_version_to_inventory(inventory, 'v1', v1_version, files)
    write_content_files(object_root, 'v1', files)
    write_inventory_files(object_root, inventory)
    v2_version = get_base_version(created='2019-12-01T12:24:59.123456Z')
    add_version_to_inventory(inventory, 'v2', v2_version, [])
    write_inventory_files(object_root, inventory)
