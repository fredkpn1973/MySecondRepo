import requests
import json

"""
Modify these please
"""
url = 'http://sbx-nxos-mgmt.cisco.com/ins'
switchuser = 'admin'
switchpassword = 'Admin_1234!'

myheaders = {'content-type': 'application/json'}
payload = {
    "ins_api": {
        "version": "1.0",
        "type": "cli_show",
        "chunk": "0",
        "sid": "1",
        "input": "show version",
        "output_format": "json"
    }
}
response = requests.post(url, data=json.dumps(
    payload), headers=myheaders, auth=(switchuser, switchpassword)).json()
