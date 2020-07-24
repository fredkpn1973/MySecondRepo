import requests
import json

target = "http://172.16.30.101/api/aaaLogin.json"
username = "cisco"
password = "cisco"

requestheader = {"content-type": "application/json"}
showcmd = {
    "ins_api": {
        "version": "1.0",
        "type": "cli_show",
        "chunk": "0",
        "sid": "1",
        "input": "show version",
        "output_format": "json"
    }
}

response = requests.post(
    target,
    data=json.dumps(showcmd),
    headers=requestheader,
    auth=(username, password),
    verify=False,
).json()

token = response

print(json.dumps(response, indent=4))
