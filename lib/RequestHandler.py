import requests
import time
import os

import json

# Read JSON file
script_dir = os.path.dirname(os.path.abspath(__file__))
ruta_completa = os.path.join(script_dir, "", "cfg.json")
with open(ruta_completa, 'r', encoding='utf-8') as file:
    data = json.load(file)
    user_ = data["user"]
    pass_ = data["password"]
    uri_ = data["uri"]
    business_ = data["businessId"]

class RequestHandler:
    def __init__(self, uri, payload=None):
        self.uri = uri
        self.payload = payload
        
    def execute(self):
        self.login()
        if self.payload != None:
            return self.requestPost()
        else:
            return self.requestGet()
        
        
    def login(self):
        url = uri_+'/auth/login/'
        payload = {
            'username': user_,
            'password': pass_
        }

        r = requests.post(url, json=payload)
        print(f"Status Code: {r.status_code}, Response: {r.json()}")

        j = r.json()
        auth = 'Token '+j['key']
        self.headers = {'Authorization': auth}
        print(self.headers)
        
    def requestPost(self):
        url2 = uri_+self.uri
        r = requests.post(url2, headers=self.headers, json=self.payload)
        j = r.json()
        print(f"Status Code: {r.status_code}, Response: {r.json()}")
        return j

    def requestGet(self):
        url3 = uri_+self.uri
        r = requests.get(url3, headers=self.headers)
        j = r.json()
        print(f"Status Code: {r.status_code}, Response: {r.json()}")
        return j
