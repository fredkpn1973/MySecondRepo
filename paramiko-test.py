#!/usr/bin/env python3
import sys
from time import sleep
import paramiko

router = "10.23.62.1"

conn = paramiko.SSHClient()
conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
conn.connect(router, username="vosko", password="Vosko123")
router_conn = conn.invoke_shell()
print('Successfully connected to %s' % router)
router_conn.send('terminal length 0\n')
sleep(1)

router_conn.send("show arp\n")
sleep(2)

print(router_conn.recv(5000).decode("utf-8"))
