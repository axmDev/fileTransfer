# PWR Test updater by Axel Ambrosio.

import os
import time
import json
import paramiko
import warnings
import configparser
from scp import SCPClient
from concurrent.futures import ThreadPoolExecutor

warnings.filterwarnings(action='ignore', module='paramiko.*')

config = configparser.ConfigParser()
config.read('exclusions.ini')
exclude_files = config.get('Exclusions', 'files').split(', ')
exclude_dirs = config.get('Exclusions', 'dirs').split(', ')

with open('hosts.json') as f:
    hosts = json.load(f)

port = 22
password = 'g00gl3flexG@'
source_dir = '/home/testusr/Desktop/PWT_Interface'


def should_exclude(filepath):
    for exclude_file in exclude_files:
        if exclude_file in filepath:
            return True

    for exclude_dir in exclude_dirs:
        if exclude_dir in filepath:
            return True
    return False


def transfer_files(host_info):
    ip = host_info['ip']
    username = host_info['username']

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port, username=username, password=password)

        with SCPClient(ssh.get_transport()) as scp:
            for root, dirs, files in os.walk(source_dir):
                dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
                for dir in dirs:
                    dirpath = os.path.join(root, dir)
                    if not should_exclude(dirpath):
                        remote_path = os.path.join('/home/testusr/Desktop/PWT_Interface/', os.path.relpath(dirpath, source_dir))
                        scp.put(dirpath, remote_path, recursive=True)
                        # print(f'Transfer {dirpath} to {ip}: {remote_path}')
                for file in files:
                    filepath = os.path.join(root, file)
                    if not should_exclude(filepath):
                        remote_path = os.path.join('/home/testusr/Desktop/PWT_Interface/',
                                                   os.path.relpath(filepath, source_dir))
                        scp.put(filepath, remote_path)
                        # print(f'Transfer {filepath} to {ip}: {remote_path}')
            print(f'Transfer to {ip} completed.')
    except paramiko.SSHException as ssh_error:
        print(f'Error SSH with {ip}: {ssh_error}')
    except Exception as e:
        print(f'Transfer error to {ip}: {e}')
    finally:
        ssh.close()


def transfer_files_with_delay(host_info):
    transfer_files(host_info)
    time.sleep(5)


with ThreadPoolExecutor(max_workers=1) as executor:
    executor.map(transfer_files_with_delay, hosts)