# -*- coding: utf-8 -*-

import getpass
import argparse
import paramiko
import re
from six import iteritems
from pprint import pprint
from collections import defaultdict
import traceback
import json

class VnxeSSH(object):
    """
    This class provides methods to manage a VNXe NAS using paramiko SSH

    """

    def __init__(self, username=None, password=None, host=None):
        """Prepare to make a connection to the VNX
        Args:
            username
            password
            host
        """

        if username is not None:
            self.username = username
        else:
            raise ValueError("Missing the required parameter `username` when calling `__init__`")

        if password is not None:
            self.password = password
        else:
            raise ValueError("Missing the required parameter `password` when calling `__init__`")

        if host is not None:
            self.host = host
        else:
            raise ValueError("Missing the required parameter `host` when calling `__init__`")


    def connect_vnx_ssh(self):
        import time
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.host,username=self.username,password=self.password)
            time.sleep(5)
            return ssh
        except Exception as e:
            print('*** Caught exception: {} : {}'.format(str(e.__class__),str(e)))
            traceback.print_exc()
            try:
                ssh.close()
            except:
                pass

    def list_nfs_exports(self):
        re_nfs_export = re.compile(r'export\W+(?P<nfs_export>(/\w+?([\/|\w]+)))\W+?(name\W+(?P<nfs_name>(/\w+?([\/|\w]+))))\W+')
        list_nfs_command = 'export NAS_DB=/nas; /nas/bin/server_export ALL -Protocol nfs -list -all'

        nfs_exports = defaultdict(list)
        try:
            ssh = self.connect_vnx_ssh()
            stdin,stdout,stderr = ssh.exec_command(list_nfs_command, get_pty=True)
            if stdout:
                for line in stdout:
                    re_nfs_export_match = re_nfs_export.search(line)
                    if re_nfs_export_match:
                        nfs_export = re_nfs_export_match.group('nfs_export')
                        nfs_name = re_nfs_export_match.group('nfs_name')

                        nfs_exports[nfs_export].append(nfs_name)

            ssh.close()

            return nfs_exports

        except Exception as e:
            print('Exception when calling `list_nfs_exports`: {}\n'.format(e))
            raise

    def list_cifs_shares(self):
        re_cifs_share = re.compile(r'share\W+(?P<share_name>\w+)\W+(?P<share_directory>(/\w+?([\/|\w]+)))\W+(?P<remainder>.*)')
        re_comment = re.compile(r'.*comment\W+(\W+.*)\W+')

        list_cifs_command = 'export NAS_DB=/nas; /nas/bin/server_export ALL -Protocol cifs -list -all'

        cifs_shares = defaultdict(list)

        try:
            ssh = self.connect_vnx_ssh()
            stdin,stdout,stderr = ssh.exec_command(list_cifs_command, get_pty=True)
            if stdout:
                for line in stdout:
                    re_cifs_share_match = re_cifs_share.search(line)
                    if re_cifs_share_match:
                        share_name = re_cifs_share_match.group('share_name')
                        share_directory = re_cifs_share_match.group('share_directory')
                        re_comment_match = re_comment.search(re_cifs_share_match.group('remainder'))
                        if re_comment_match:
                            comment = re_comment_match.group(1)
                        else:
                            comment = "No Comment"


                        cifs_shares[share_name].append(share_directory)

            ssh.close()

            return cifs_shares

        except Exception as e:
            print('Exception when calling `list_cifs_shares`: {}\n'.format(e))
            raise

    def list_cifs_share_connections(self):
        re_start = re.compile(r'^\W+SMB2 session Id=.*')
        re_user = re.compile(r'^\W+Uid=(.*)\WNTcred\(.*\)\W+(?P<USER>(\w+\\\w+))\W+$')
        re_client = re.compile(r'^\|\|\|\|\W+AUDIT.*Client\((.*)\).*')
        re_nas = re.compile(r'^\W+(\w+)\[\w+\]\W+on\W+if=(\w+)$')
        re_path = re.compile(r'^\W+Absolute path of the share=(.*)$')

        cifs_connections = defaultdict(list)

        list_cifs_connections_command = 'export NAS_DB=/nas; /nas/bin/server_cifs ALL -option audit'

        try:
            ssh = self.connect_vnx_ssh()
            stdin,stdout,stderr = ssh.exec_command(list_cifs_connections_command, get_pty=True)
            if stdout:
                in_stanza = False
                for line in stdout:
                    line = line.strip()
                    if 'SMB2 session Id=' in line:
                        in_stanza = True
                    if in_stanza:
                        re_user_match = re_user.search(line)
                        if re_user_match:
                            uline = re_user_match.group('USER')
                        re_client_match = re_client.search(line)
                        if re_client_match:
                            try:
                                cline = re_client_match.group(1)
                                cline_uline = '{}:{}'.format(cline,uline)
                            except:
                                cline_uline = '{}:{}'.format(cline,None)
                                pass
                        re_nas_match = re_nas.search(line)
                        if re_nas_match:
                            nasname = re_nas_match.group(1)
                            nasname = nasname.lower()
                        re_path_match = re_path.search(line)
                        if re_path_match:
                            pline = re_path_match.group(1)
                            if pline != '':
                                pline = pline.replace('\\', '/')
                                pline = '{}:{}'.format(nasname,pline.replace('\\', '/'))
                                cifs_connections[pline].append(cline_uline)
                            in_stanza = False

            ssh.close()
            data = json.loads(json.dumps(cifs_connections))
            return data
        except Exception as e:
            print('Exception when calling `list_cifs_shares`: {}\n'.format(e))
            raise

def getargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n','--nas',
                        action='store',
                        dest='nas',
                        required=True,
                        help='Name or IP of OneFS system')
    parser.add_argument('-u','--username',
                        action='store',
                        dest='username',
                        required=True,
                        help='Name of user with access to the OneFS API')
    parser.add_argument('-p','--password',
                        action='store',
                        dest='password',
                        required=True,
                        help='Password')
    parser.add_argument('--list_shares',
                        action='store_true',
                        dest='list_shares',
                        required=False,
                        help='Display CIFS shares on the VNXe')
    parser.add_argument('--list_connections',
                        action='store_true',
                        dest='list_connections',
                        help='List all connections')
    parser.add_argument('--list_exports',
                        action='store_true',
                        dest='list_exports',
                        help='List NFS exports on the VNX')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = getargs()
    P = VnxeSSH(username=args.username,
                password=args.password,
                host=args.nas)

    if args.list_shares:
        cifs_shares = P.list_cifs_shares()
        pprint(cifs_shares)
    if args.list_exports:
        nfs_exports = P.list_nfs_exports()
        pprint(nfs_exports)
    if args.list_connections:
        cifs_connections = P.list_cifs_share_connections()
        pprint(cifs_connections, depth=4)
        fname = '{}.json'.format(args.nas)
        with open(fname, "w") as outfile:
            json.dump(cifs_connections,outfile, indent=4)

