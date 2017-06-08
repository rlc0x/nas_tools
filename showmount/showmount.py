import re
import traceback
import os
import subprocess
from collections import defaultdict
import argparse
from pprint import pprint
import json

class ShowMount(object):
    def __init__(self, nas=None, base=None):
        if nas is not None:
            self.nas = nas
        else:
            raise ValueError('Name or IP address of the nas is required')

        if base is not None:
            self.base = base
        else:
            raise ValueError('Pattern to ignore when looping through mounts is required')


        self.re_nfs_alias = re.compile('(?P<nfs_alias>(/\w+))$')
        self.re_nas_clients = re.compile('(?P<nfs_client>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})|(\w+)?([\.|\w]+)):(?P<vfs_client>(.\w+?([\/|\w]+)))')
        self.nas_clients = defaultdict(list)
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
                    vfs = re_nas_clients_match.group('vfs_client').strip().split('/')
                    if self.base in vfs[1]:
                        vfs = '/{}'.format(vfs[2])
                    else:
                        vfs = '/{}'.format(vfs[1])
                    self.nas_clients[vfs].append(client_name)
            except:
                pass
        return self.nas_clients

def getargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n','--nas',
                        action='store',
                        required=True,
                        dest='nas',
                        help='Name of the NAS to querry')
    parser.add_argument('-b','--base',
                        action='store',
                        required=True,
                        dest='base',
                        help='Name of the Virtual Filesystem base to exclude when looking for matching directories')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = getargs()
    SM = ShowMount(nas=args.nas,base=args.base)
    nas_client_list = SM.get_nas_clients()
    if nas_client_list:
        pprint(nas_client_list)
