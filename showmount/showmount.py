import re
import traceback
import os
import subprocess
from collections import defaultdict
import argparse
from pprint import pprint
import json

class ShowMount(object):
    def __init__(self, nas=None):
        if nas is not None:
            self.nas = nas
        else:
            raise ValueError('Name or IP address of the nas is required')

        self.re_nfs_alias = re.compile('(?P<nfs_alias>(/\w+))$')
        self.re_nas_clients = re.compile('(?P<nfs_client>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})|(\w+)?([\.|\w]+)):(?P<vfs_client>(.\w+?([\/|\w]+)))')
        self.nas_clients = defaultdict(lambda: defaultdict(list))
        self.nas_clients_cmd = 'showmount --no-headers -a {}'.format(self.nas)
        self.vfs_dirs_cmd = 'showmount --no-headers -e {}'.format(self.nas)

    def get_vfs_dirs(self):
        vfs_dirs = set()
        for line in subprocess.Popen(self.vfs_dirs_cmd, shell=True, stdout=subprocess.PIPE).communicate()[0].decode('utf-8').split('\n'):
            line = line.strip().split(' ')
            '''
            The format returned could be either the full path to the share, or just the alias
            '''
            re_nfs_alias_match = self.re_nfs_alias.search(line[0])
            if re_nfs_alias_match:
                nfs_alias = re_nfs_alias_match.group('nfs_alias')
                vfs_dirs.add(nfs_alias)
        return vfs_dirs

    def get_nas_clients(self):
        for line in subprocess.Popen(self.nas_clients_cmd, shell=True, stdout=subprocess.PIPE).communicate()[0].decode('utf-8').split('\n'):
            try:
                re_nas_clients_match = self.re_nas_clients.search(line)
                if re_nas_clients_match:
                    client_name = re_nas_clients_match.group('nfs_client')
                    vfs = re_nas_clients_match.group('vfs_client')
                    nas_clients[self.nas][vfs].append(client_name)
            except:
                pass
        return nas_clients

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
    nas_client_list = SM.get_vfs_dirs()
    if nas_client_list:
        print(json.dumps(str(nas_client_list), indent=4))
