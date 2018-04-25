# -*- coding: utf8 -*-
from requests import Request, Session
import shutil
import csv
from netaddr import IPAddress, IPNetwork, cidr_merge
from collections import Counter

url = 'https://raw.githubusercontent.com/zapret-info/z-i/master/dump.csv'
file_name = 'dump.csv'
download = False
last = ''
MIN_HOSTS_FOR_JOIN = 32

try:
    f = open('dump_mod.txt', 'r')
    last = f.readline()
    f.close()
except:
    print("File doesn't exist: dump_mod.txt")

s = Session()
req = Request('GET', url, headers={"If-Modified-Since": last})
prepped = req.prepare()
resp = s.send(prepped, stream=True)
if resp.status_code == 200:
    changed = last != resp.headers['ETag']
    if changed:
        print("Changed since " + last + "... Downloading...")
        with open(file_name, 'wb') as f:
            resp.raw.decode_content = True
            shutil.copyfileobj(resp.raw, f)
            last = resp.headers['ETag']
            f = open('dump_mod.txt', 'w')
            try:
                f.writelines(last)
            finally:
                f.close()
    else:
        print("Not changed, skipping")
else:
    if resp.status_code == 304:
        print("Didn't change")
    else:
        print("Download error: " + resp.status_code)

f = open(file_name, encoding='cp1251', mode='rt')
try:
    reader = csv.reader(f, delimiter=';')
    ip_list = []
    for row in reader:
        ips = str(row[0]).split('|')
        for ip in ips:
            try:
                if "Updated" in ip:
                    continue
                if ip.strip() == "":
                    continue
                if "/" not in ip:
                    ip_net = IPNetwork(ip.strip()+"/32")
                else:
                    ip_net = IPNetwork(ip.strip())
                ip_list.append(ip_net)
            except:
                print("Error adding IP/NET: " + ip.strip())

    print(str(len(ip_list)) + " total records in ZapretInfo list")
    merged_list = cidr_merge(ip_list)
    print(str(len(merged_list)) + " records cleaned and summarized in ZapretInfo list")
finally:
    f.close()


banned = 0
shorten = Counter()
for net in merged_list:
    banned += net.size
    addr, mask = str(net).rsplit('/', 1)
    if int(mask) > 24:
        shorten[addr.rsplit('.',1)[0]] += net.size

joined_networks = []

for k,v in shorten.most_common():
    if v < MIN_HOSTS_FOR_JOIN:
        break
    joined_networks.append(IPNetwork(k + '/24'))
short_list = cidr_merge(merged_list + joined_networks) if joined_networks else merged_list

print(str(len(short_list)) + " records in summarized list (more than " + str(MIN_HOSTS_FOR_JOIN) + " addresses in /24 network are substituted with /24 network record)")