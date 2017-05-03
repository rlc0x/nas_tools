#!/bin/env python

import re,traceback,os,xlwt
from subprocess import *
from collections import defaultdict
d = {}
wbk = xlwt.Workbook()
fs_style = xlwt.easyxf('font: color_index black, name Lucida Console; align: wrap on, vert center, horiz center;')
header_style = xlwt.easyxf('font: color_index black, name Lucida Console, bold on; align: wrap on, vert center, horiz center;')
server_style = xlwt.easyxf('font: color_index black, name Lucida Console, bold off; align: wrap on, vert center, horiz left;')

def getbase(nas):
    nasfs = set()
    for line in Popen(['showmount', '--no-headers', '-e', nas], stdout=PIPE).communicate()[0].split('\n')[1:]:
        line = line.strip().split(' ').pop(0)
        line = line.split('/')
        if line[-1] == "":
            continue
        else:
            nasfs.add(line[-1])
    return nasfs

def getnassys(nas):
    nassys = []
    for line in Popen(['showmount', '--no-headers', '-a', nas], stdout=PIPE).communicate()[0].split('\n'):
        try:
            line = line.strip().split(':')
            if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', line[0]):
                sname = line[0]
            else:
                sname = line[0].split('.').pop(0)
            mount = line[1].split('/')
            if re.match(r'root.*', mount[1]):
                nassys.append((sname,mount[2]))
            else:
                nassys.append((sname,mount[1]))
        except:
            pass
    return nassys

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--nas", action="store", dest="nas",   help="Provide the NAS to gather FS info from")
    parser.add_argument("-f", "--file", action="store", dest="fname",  help="Provide a list of NAS devices to gather FS info from")
    parser.add_argument("-x", action="store_true", dest="xl",  help="Create an Excel doc based on the results")
    args = parser.parse_args()

    if args.nas:
        naslist = []
        naslist.append(args.nas)
        xlsfile = args.nas + ".xls"
    elif args.fname:
        xlsfile = "site_nfs_mounts.xls"
        naslist = set()
        with open(args.fname, 'r') as f:
            for nas in f:
                nas = nas.strip()
                print nas
                naslist.add(nas)
    else:
        print "Missing required -n/--nas OR -f/--file arguments"
        os._exit(1)

    for nas in naslist:
        nasfs = getbase(nas)
        nassys = getnassys(nas)
        row = 0
        sheet = wbk.add_sheet(nas)
        sheet.col(0).width = 7400
        sheet.write(row,0,'NFS NAS Mount', header_style)
        sheet.write(row,1,'Systems Accessing NFS NAS Mount', header_style)
        row +=1
        xl_dict = {}
        for nasmount in nasfs:
            hosts = set()
            for sysmount in nassys:
                if str(sysmount[1]) in str(nasmount):
                    hosts.add(sysmount[0])
                xl_dict = defaultdict(list)
                for host in hosts:
                    xl_dict[nasmount].append(host)

            if args.xl:

                for key, value in xl_dict.items():
                    sheet.col(0).width = 7400
                    sheet.write(row,0,key, server_style)
                    sheet.col(1).width = 35200
                    sheet.write(row,1,','.join(value), fs_style)
                    wbk.save(xlsfile)
                    row +=1
            else:
                for key, value in xl_dict.items():
                    print key, ','.join(value)

if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        print str(e)
        traceback.print_exc()
        os._exit(1)
