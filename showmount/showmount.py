import re
import traceback
import os
import subprocess
from collections import defaultdict
import argparse
from pprint import pprint
import json

class ShowMount(object):
    def __init__(self, session):
        self.log = logging.getLogger(__name__)
        self.log.addHandler(logging.NullHandler())
        self.session = session

    def __init__(self, ip=None):
        if ip is not None:
            self.nas = ip
        else:
            raise ValueError('Name of the nas is required')

    def get_vfs_dirs(self):
        vfs_dirs = []
        vfs_dirs_cmd = 'showmount --no-headers -e {}'.format(self.nas)
        for line in subprocess.Popen(vfs_dirs_cmd, shell=True, stdout=subprocess.PIPE).communicate()[0].decode('utf-8').split('\n'):
            line = line.strip().split(' ')
            if re.match(r'/root_vdm.*', line[0]):
                vfs_dirs.append(line[0])
        return vfs_dirs 
            
    def get_nas_clients(self):
        nas_clients = defaultdict(list)
        nas_clients_cmd = 'showmount --no-headers -a {}'.format(self.nas)
        re_nas_clients = re.compile('(?P<nfs_client>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})|(\w+)?([\.|\w]+)):(?P<vfs_client>(.\w+?([\/|\w]+)))')
        for line in subprocess.Popen(nas_clients_cmd, shell=True, stdout=subprocess.PIPE).communicate()[0].decode('utf-8').split('\n'):
            try:
                re_nas_clients_match = re_nas_clients.search(line)
                if re_nas_clients_match:
                    client_name = re_nas_clients_match.group('nfs_client')
                    vfs = re_nas_clients_match.group('vfs_client')
                if re.match(r'/root_vdm.*', vfs):
                    nas_clients[vfs].append(client_name)
                elif re.match(r'/(\w+).*',vfs):
                    nas_clients[vfs].append(client_name)
            except:
                pass
        data = json.loads(json.dumps(nas_clients))
        return data

def getargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n','--nas',
                        action='store',
                        required=True,
                        dest='nas',
                        help='Name of the NAS to querry')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = getargs()
    SM = ShowMount(nas=args.nas)
    nas_client_list = SM.get_nas_clients()
    if nas_client_list:
        pprint(nas_client_list, depth=4)
