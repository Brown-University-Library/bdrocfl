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
    inventory_path = os.path.join(object_root, 'inventory.json')
    version_inventory_path = os.path.join(object_root, inventory['head'], 'inventory.json')
    inventory_hash_path = os.path.join(object_root, 'inventory.json.sha512')
    version_inventory_hash_path = os.path.join(object_root, inventory['head'], 'inventory.json.sha512')
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


def create_object(storage_root, pid, files=(('file1', b'abcd'),)):
    object_root = ocfl.object_path(storage_root, pid)
    os.makedirs(object_root, exist_ok=False)
    v1_content = os.path.join('v1', 'content')
    os.makedirs(os.path.join(object_root, v1_content), exist_ok=False)
    v1_version = get_base_version()
    inventory = get_base_inventory(pid)
    for file_tuple in files:
        file_name, file_content = file_tuple
        file_path = os.path.join(v1_content, file_name)
        file_hash = hashlib.sha512(file_content).hexdigest()
        if file_hash in inventory['manifest']:
            inventory['manifest'][file_hash].append(file_path)
        else:
            inventory['manifest'][file_hash] = [file_path]
        if file_hash in v1_version['state']:
            v1_version['state'][file_hash].append(file_name)
        else:
            v1_version['state'][file_hash] = [file_name]
        with open(os.path.join(object_root, file_path), 'wb') as f:
            f.write(file_content)
    inventory['versions']['v1'] = v1_version
    inventory['head'] = 'v1'
    write_inventory_files(object_root, inventory)


def create_deleted_object(storage_root, pid, files=(('file1', b'abcd'),)):
    object_root = ocfl.object_path(storage_root, pid)
    os.makedirs(object_root, exist_ok=False)
    v1_content = os.path.join('v1', 'content')
    os.makedirs(os.path.join(object_root, v1_content), exist_ok=False)
    v1_version = get_base_version()
    inventory = get_base_inventory(pid)
    for file_tuple in files:
        file_name, file_content = file_tuple
        file_path = os.path.join(v1_content, file_name)
        file_hash = hashlib.sha512(file_content).hexdigest()
        if file_hash in inventory['manifest']:
            inventory['manifest'][file_hash].append(file_path)
        else:
            inventory['manifest'][file_hash] = [file_path]
        if file_hash in v1_version['state']:
            v1_version['state'][file_hash].append(file_name)
        else:
            v1_version['state'][file_hash] = [file_name]
        with open(os.path.join(object_root, file_path), 'wb') as f:
            f.write(file_content)
    inventory['versions']['v1'] = v1_version
    inventory['head'] = 'v1'
    write_inventory_files(object_root, inventory)
    v2_content = os.path.join('v2', 'content')
    os.makedirs(os.path.join(object_root, v2_content), exist_ok=False)
    v2_version = get_base_version(created='2019-12-01T12:24:59.123456Z')
    inventory['versions']['v2'] = v2_version
    inventory['head'] = 'v2'
    write_inventory_files(object_root, inventory)
