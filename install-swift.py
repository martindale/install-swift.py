#!/usr/bin/python

from os import system
from datetime import datetime

'''
This is a python script to install swift in an empty ubuntu environment.
It automatically deploy and config all things described in "SAIO - Swift All In One".

http://swift.openstack.org/development_saio.html

This script will use a loopback device for storage.
run this script as root.

Tested under ubuntu 12.04.
Originally by jadesoul <wslgb2006@gmail.com>
Updates by martindale <eric@ericmartindale.com>
'''

def fread(path):
  f=open(path)
  s=f.read()
  f.close()
  return s
  
def fwrite(s, path, append=False):
  f=open(path, 'a' if append else 'w')
  f.write(s)
  f.close()
  
def fappend(s, path):
  fwrite(s, path, True)
  
def run(cmd):
  cmds=cmd.strip().split('\n')
  for cmd in cmds:
    cmd=cmd.strip()
    if not cmd or cmd[0]=='#': continue
    print '@', datetime.now(), 'CMD:', cmd
    system(cmd)

# make preparations for apt
# =================

preparations_for_apt='''
# seems these are not needed
# add-apt-repository ppa:swift-core/release
# apt-get update


groupadd swift
useradd -g swift swift
usermod -G swift swift
'''
run(preparations_for_apt)

# install required packages
# ================

required_packages='''
rsync # comment is supported here
git
subversion
openssh-server
# ftpd  # uncomment to install it if you like
curl
gcc
git-core
memcached
sqlite3
xfsprogs
python-dev
python-setuptools
python-pip
python-software-properties
python-cjson
python-simplejson
python-configobj
python-coverage
python-nose
python-xattr
python-webob
python-eventlet
python-greenlet
python-pastedeploy
python-netifaces
'''
required_packages=[i[:(i+'#').find('#')] for i in required_packages.strip().split('\n')]
required_packages=[i.strip() for i in required_packages if i.strip()]
run('apt-get install %s' % ' '.join(required_packages))


# setup virtual storage device
# ==================

# using a loopback device for storage
run('''
mkdir /srv

# (modify seek to make a larger or smaller partition)
dd if=/dev/zero of=/srv/swift-disk bs=1024 count=0 seek=50000000

mkfs.xfs -i size=1024 /srv/swift-disk
''')

# add a line in fstab file
line='''
/srv/swift-disk /mnt/sdb1 xfs loop,noatime,nodiratime,nobarrier,logbufs=8 0 0
'''
fp='/etc/fstab'
if not line in fread(fp): fappend(line, fp)

# Create and populate configuration directories
run('''
mkdir /mnt/sdb1
mount /mnt/sdb1

mkdir /mnt/sdb1/1 /mnt/sdb1/2 /mnt/sdb1/3 /mnt/sdb1/4
chown swift:swift /mnt/sdb1/*

ln -fs /mnt/sdb1/1 /srv/1
ln -fs /mnt/sdb1/2 /srv/2
ln -fs /mnt/sdb1/3 /srv/3
ln -fs /mnt/sdb1/4 /srv/4

mkdir -p /etc/swift/object-server /etc/swift/container-server /etc/swift/account-server /srv/1/node/sdb1 /srv/2/node/sdb2 /srv/3/node/sdb3 /srv/4/node/sdb4 /var/run/swift
chown -R swift:swift /etc/swift /srv/1/ /srv/2/ /srv/3/ /srv/4/ /var/run/swift
''')

# make these two lines before exit 0
before_exit_0='''
mkdir /var/run/swift
chown swift:swift /var/run/swift
exit 0
'''
fp='/etc/rc.local'
s=fread(fp)
if not before_exit_0 in s: fwrite(s.replace('\nexit 0', before_exit_0), fp)

# setting config files
# ============

fp='/etc/rsyncd.conf'
s='''
uid = swift
gid = swift
log file = /var/log/rsyncd.log
pid file = /var/run/rsyncd.pid
address = 127.0.0.1

[account6012]
max connections = 25
path = /srv/1/node/
read only = false
lock file = /var/lock/account6012.lock

[account6022]
max connections = 25
path = /srv/2/node/
read only = false
lock file = /var/lock/account6022.lock

[account6032]
max connections = 25
path = /srv/3/node/
read only = false
lock file = /var/lock/account6032.lock

[account6042]
max connections = 25
path = /srv/4/node/
read only = false
lock file = /var/lock/account6042.lock


[container6011]
max connections = 25
path = /srv/1/node/
read only = false
lock file = /var/lock/container6011.lock

[container6021]
max connections = 25
path = /srv/2/node/
read only = false
lock file = /var/lock/container6021.lock

[container6031]
max connections = 25
path = /srv/3/node/
read only = false
lock file = /var/lock/container6031.lock

[container6041]
max connections = 25
path = /srv/4/node/
read only = false
lock file = /var/lock/container6041.lock


[object6010]
max connections = 25
path = /srv/1/node/
read only = false
lock file = /var/lock/object6010.lock

[object6020]
max connections = 25
path = /srv/2/node/
read only = false
lock file = /var/lock/object6020.lock

[object6030]
max connections = 25
path = /srv/3/node/
read only = false
lock file = /var/lock/object6030.lock

[object6040]
max connections = 25
path = /srv/4/node/
read only = false
lock file = /var/lock/object6040.lock
'''
fwrite(s, fp)

# enable rsync service
fp='/etc/default/rsync'
ss=fread(fp).split('\n')
ss=['RSYNC_ENABLE=true' if s.startswith('RSYNC_ENABLE=') else s for s in ss]
fwrite('\n'.join(ss), fp)
run('service rsync restart')

# Optional: Setting up rsyslog for individual logging
fp='/etc/rsyslog.d/10-swift.conf'
s='''
# Uncomment the following to have a log containing all logs together
# local1,local2,local3,local4,local5.*   /var/log/swift/all.log

# Uncomment the following to have hourly proxy logs for stats processing
#$template HourlyProxyLog,"/var/log/swift/hourly/%$YEAR%%$MONTH%%$DAY%%$HOUR%"
#local1.*;local1.!notice ?HourlyProxyLog

local1.*;local1.!notice /var/log/swift/proxy.log
local1.notice           /var/log/swift/proxy.error
local1.*                ~

local2.*;local2.!notice /var/log/swift/storage1.log
local2.notice           /var/log/swift/storage1.error
local2.*                ~

local3.*;local3.!notice /var/log/swift/storage2.log
local3.notice           /var/log/swift/storage2.error
local3.*                ~

local4.*;local4.!notice /var/log/swift/storage3.log
local4.notice           /var/log/swift/storage3.error
local4.*                ~

local5.*;local5.!notice /var/log/swift/storage4.log
local5.notice           /var/log/swift/storage4.error
local5.*                ~
'''
fwrite(s, fp)

# modify Configuration file for rsyslog
fp='/etc/rsyslog.conf'
ss=fread(fp).split('\n')
ss=['$PrivDropToGroup adm' if s.startswith('$PrivDropToGroup syslog') else s for s in ss]
fwrite('\n'.join(ss), fp)

# restart rsyslog service
run('''
mkdir -p /var/log/swift/hourly
chown -R syslog:adm /var/log/swift
service rsyslog restart
''')


# Getting the code and setting up test environment  
run('''
mkdir ~/bin

# Check out the swift repo with git clone 
cd ~ ; git clone https://github.com/openstack/swift.git
# cd ~ ; git clone git://jadesoul-dev/swift.git
# cd ~ ; tar zxvf swift.tgz

# Build a development installation of swift
# cd ~/swift; python setup.py develop # this would cause bugs
cd ~/swift; python setup.py install # this works fine
''')

# Edit ~/.bashrc
fp='/root/.bashrc'
exports='''
export SWIFT_TEST_CONFIG_FILE=/etc/swift/test.conf
export PATH=${PATH}:~/bin
'''
if not exports in fread(fp): fappend(exports, fp)

run('. ~/.bashrc')

fp='/etc/swift/proxy-server.conf'
s='''[DEFAULT]
bind_port = 8080
user = swift
log_facility = LOG_LOCAL1

[pipeline:main]
pipeline = healthcheck cache tempauth proxy-server

[app:proxy-server]
use = egg:swift#proxy
allow_account_management = true
account_autocreate = true

[filter:tempauth]
use = egg:swift#tempauth
user_admin_admin = admin .admin .reseller_admin
user_test_tester = testing .admin
user_test2_tester2 = testing2 .admin
user_test_tester3 = testing3

[filter:healthcheck]
use = egg:swift#healthcheck

[filter:cache]
use = egg:swift#memcache
'''
fwrite(s, fp)


fp='/etc/swift/swift.conf'
s='''
[swift-hash]
# random unique string that can never change (DO NOT LOSE)
swift_hash_path_suffix = ksdhfa98y29jhkjhk
'''
fwrite(s, fp)


# for account server config
tpl='''
[DEFAULT]
devices = /srv/%d/node
mount_check = false
bind_port = 60%d2
user = swift
log_facility = LOG_LOCAL%d

[pipeline:main]
pipeline = account-server

[app:account-server]
use = egg:swift#account

[account-replicator]
vm_test_mode = yes

[account-auditor]

[account-reaper]
'''
for i in range(1, 4+1):
  s=tpl % (i, i, i+1)
  fp='/etc/swift/account-server/%d.conf' % i
  fwrite(s, fp)

# for container server config
tpl='''
[DEFAULT]
devices = /srv/%d/node
mount_check = false
bind_port = 60%d1
user = swift
log_facility = LOG_LOCAL%d

[pipeline:main]
pipeline = container-server

[app:container-server]
use = egg:swift#container

[container-replicator]
vm_test_mode = yes

[container-updater]

[container-auditor]

[container-sync]
'''
for i in range(1, 4+1):
  s=tpl % (i, i, i+1)
  fp='/etc/swift/container-server/%d.conf' % i
  fwrite(s, fp)
  
  
# for object server config
tpl='''
[DEFAULT]
devices = /srv/%d/node
mount_check = false
bind_port = 60%d0
user = swift
log_facility = LOG_LOCAL%d

[pipeline:main]
pipeline = object-server

[app:object-server]
use = egg:swift#object

[object-replicator]
vm_test_mode = yes

[object-updater]

[object-auditor]
'''
for i in range(1, 4+1):
  s=tpl % (i, i, i+1)
  fp='/etc/swift/object-server/%d.conf' % i
  fwrite(s, fp)
  
run('swift-init all stop')
  
fp='/root/bin/resetswift'
s='''#!/bin/bash

swift-init all stop
find /var/log/swift -type f -exec rm -f {} \;
sudo umount /mnt/sdb1
sudo mkfs.xfs -f -i size=1024 /srv/swift-disk
sudo mount /mnt/sdb1
sudo mkdir /mnt/sdb1/1 /mnt/sdb1/2 /mnt/sdb1/3 /mnt/sdb1/4
sudo chown swift:swift /mnt/sdb1/*
mkdir -p /srv/1/node/sdb1 /srv/2/node/sdb2 /srv/3/node/sdb3 /srv/4/node/sdb4
sudo rm -f /var/log/debug /var/log/messages /var/log/rsyncd.log /var/log/syslog
sudo service rsyslog restart
sudo service memcached restart
'''
fwrite(s, fp)



fp='/root/bin/remakerings'
s='''#!/bin/bash

cd /etc/swift

rm -f *.builder *.ring.gz backups/*.builder backups/*.ring.gz

swift-ring-builder object.builder create 18 3 1
swift-ring-builder object.builder add z1-127.0.0.1:6010/sdb1 1
swift-ring-builder object.builder add z2-127.0.0.1:6020/sdb2 1
swift-ring-builder object.builder add z3-127.0.0.1:6030/sdb3 1
swift-ring-builder object.builder add z4-127.0.0.1:6040/sdb4 1
swift-ring-builder object.builder rebalance
swift-ring-builder container.builder create 18 3 1
swift-ring-builder container.builder add z1-127.0.0.1:6011/sdb1 1
swift-ring-builder container.builder add z2-127.0.0.1:6021/sdb2 1
swift-ring-builder container.builder add z3-127.0.0.1:6031/sdb3 1
swift-ring-builder container.builder add z4-127.0.0.1:6041/sdb4 1
swift-ring-builder container.builder rebalance
swift-ring-builder account.builder create 18 3 1
swift-ring-builder account.builder add z1-127.0.0.1:6012/sdb1 1
swift-ring-builder account.builder add z2-127.0.0.1:6022/sdb2 1
swift-ring-builder account.builder add z3-127.0.0.1:6032/sdb3 1
swift-ring-builder account.builder add z4-127.0.0.1:6042/sdb4 1
swift-ring-builder account.builder rebalance
'''
fwrite(s, fp)



fp='/root/bin/startmain'
s='''#!/bin/bash

swift-init main start
'''
fwrite(s, fp)



fp='/root/bin/startrest'
s='''#!/bin/bash

swift-init rest start
'''
fwrite(s, fp)


#stop all
fp='/root/bin/stopall'
s='''#!/bin/bash

swift-init all stop
'''
fwrite(s, fp)


fp='/root/bin/pgrepswift'
s='''#!/bin/bash

ps aux | grep swift
'''
fwrite(s, fp)



run('''
chmod +x ~/bin/*
~/bin/remakerings
cd ~/swift; ./.unittests
~/bin/startmain

cp ~/swift/test/sample.conf /etc/swift/test.conf

curl -v -H 'X-Storage-User: test:tester' -H 'X-Storage-Pass: testing' http://127.0.0.1:8080/auth/v1.0

# Check that swift works
swift -A http://127.0.0.1:8080/auth/v1.0 -U test:tester -K testing stat

echo curl -v -H 'X-Auth-Token: <token-from-x-auth-token-above>' <url-from-x-storage-url-above>

# Note: functional tests will first delete everything in the configured accounts
# cp ~/swift/test/functional/sample.conf /etc/swift/func_test.conf
# cd ~/swift; ./.functests

# Note: probe tests will reset your environment as they call resetswift for each test
# cd ~/swift; ./.probetests 

''')

'''
# some quick notes
# Check that swift works
swift -v -A http://127.0.0.1:8080/auth/v1.0 -U test:tester -K testing stat
swift -v -A http://127.0.0.1:8080/auth/v1.0 -U test:tester -K testing list images
swift -v -A http://127.0.0.1:8080/auth/v1.0 -U test:tester -K testing upload images test.data
swift -v -A http://127.0.0.1:8080/auth/v1.0 -U test:tester -K testing download images test.data



curl -k -D - -H 'X-Storage-User: test:tester' -H 'X-Storage-Pass: testing' http://127.0.0.1:8080/auth/v1.0

HTTP/1.1 200 OK
X-Storage-Url: http://127.0.0.1:8080/v1/AUTH_test
X-Storage-Token: AUTH_tkbf3cb494b8f749b7b34b6d26ac74297b
X-Auth-Token: AUTH_tkbf3cb494b8f749b7b34b6d26ac74297b
Content-Length: 0
Date: Thu, 31 May 2012 15:47:44 GMT


curl -k -X HEAD -D -  -H 'X-Auth-Token: AUTH_tkbf3cb494b8f749b7b34b6d26ac74297b' http://127.0.0.1:8080/v1/AUTH_test
HTTP/1.1 204 No Content
X-Account-Object-Count: 0
X-Timestamp: 1338476353.78581
X-Account-Bytes-Used: 0
X-Account-Container-Count: 0
Accept-Ranges: bytes
Content-Length: 0
Date: Thu, 31 May 2012 15:49:34 GMT


curl -k -X GET -H 'X-Auth-Token: AUTH_tkbf3cb494b8f749b7b34b6d26ac74297b' http://127.0.0.1:8080/v1/AUTH_test/images

curl -k -X GET -H 'X-Auth-Token: AUTH_tkbf3cb494b8f749b7b34b6d26ac74297b' http://127.0.0.1:8080/v1/AUTH_test/images?format=xml

#create container and upload object
curl -k -X PUT -T ./test.data -H 'Content-Type: text/plain' -H 'X-Auth-Token: AUTH_tkbf3cb494b8f749b7b34b6d26ac74297b' http://127.0.0.1:8080/v1/AUTH_test/images/test.data
curl -k -X PUT -H 'Content-Type: text/plain' -H 'X-Auth-Token: AUTH_tkbf3cb494b8f749b7b34b6d26ac74297b' http://127.0.0.1:8080/v1/AUTH_test/images

#download object
curl -k -X GET -H 'X-Auth-Token: AUTH_tkbf3cb494b8f749b7b34b6d26ac74297b' http://127.0.0.1:8080/v1/AUTH_test/images/test.data -o test2.data
curl -k -X GET -H 'X-Auth-Token: AUTH_tkbf3cb494b8f749b7b34b6d26ac74297b' http://127.0.0.1:8080/v1/AUTH_test/images/.bashrc
'''
