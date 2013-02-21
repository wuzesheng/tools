#!/usr/bin/env python
#

import csv
import os
import pexpect
import subprocess
import sys

def parse_host_file(host_file):
  file = open(host_file, 'r')
  csv_reader = csv.reader(file, delimiter=' ', skipinitialspace=True)

  host_list = list()
  for line in csv_reader:
    # TODO: check the input format
    host_list.append(line)
  file.close()
  return host_list

def generate_public_key():
  home_path = os.path.expanduser('~')
  rsa_file = '%s/.ssh/id_rsa' % home_path
  dsa_file = '%s/.ssh/id_dsa' % home_path

  if os.path.isfile(rsa_file):
    return '%s.pub' % rsa_file
  elif os.path.isfile(dsa_file):
    return '%s.pub' % dsa_file
  else:
    cmd = "ssh-keygen -t rsa -P '' -f %s" % rsa_file
    subprocess.check_call(cmd, shell=True)
    return '%s.pub' % rsa_file

def scp(host, user, passwd, local_file, remote_file):
  child = pexpect.spawn('scp %s %s@%s:%s' % (local_file,
        user, host, remote_file))
  print child.args

  ret = child.expect(['yes/no.*', 'password.*'])
  if ret == 0:
    child.sendline('yes')
    child.expect('password.*', timeout=10)
    child.sendline(passwd)
  elif ret == 1:
    child.sendline(passwd)
  else:
    print 'Error occured when execute expect()'
    sys.exit(-2)

  return child.expect([pexpect.EOF, pexpect.TIMEOUT])

def remote_exec(host, user, passwd, cmd):
  child = pexpect.spawn('ssh %s@%s "%s"' % (user, host, cmd))
  print child.args

  ret = child.expect(['yes/no.*', 'password.*'], timeout=10)
  if ret == 0:
    child.sendline('yes')
    child.expect('password.*', timeout=10)
    child.sendline(passwd)
  elif ret == 1:
    child.sendline(passwd)
  else:
    print 'Error occured when execute expect()'
    sys.exit(-3)

  return child.expect([pexpect.EOF, pexpect.TIMEOUT])

def make_authentication(key, host, user, passwd):
  # Copy public key to remote host
  if scp(host, 'root', passwd, key, '/home/%s/.ssh/key.tmp' % user) == 0:
    # Add public key to the end of '~/.ssh/authorized_keys'
    ssh_home = '/home/%s/.ssh' % user
    if 0 == remote_exec(host, 'root', passwd,
        'cd %s; cat key.tmp >> authorized_keys; rm key.tmp' % ssh_home):
      print 'Authenticate host %s successfully!' % host
    else:
      print 'Authenticate host %s timeout!' % host

def main(host_file):
  key_file = generate_public_key()

  host_list = parse_host_file(host_file)
  for host_info in host_list:
    make_authentication(key_file, host_info[0], host_info[1], host_info[2])

if __name__ == '__main__':
  if len(sys.argv) != 2:
    print 'Usage: %s host_list_file' % os.path.basename(sys.argv[0])
    print 'Host list file format: host user passwd'
    print '   - host: the remote server\'s host, can be ip or hostname'
    print '   - user: the to be autherized username'
    print '   - passwd: the root password'
    sys.exit(-1)
  else:
    main(sys.argv[1])
