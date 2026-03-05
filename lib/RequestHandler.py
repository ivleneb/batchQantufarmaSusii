import requests
import time
import os

import json

# Read JSON file
import sys
sys.path.append(r'../')
from lib.QantuConfiguration import QantuConfiguration

config = QantuConfiguration()
# credentials
business_ = config.business_
user_ = config.user_
pass_ = config.pass_
uri_ = config.uri_

class RequestHandler:
    def __init__(self, uri, payload=None, businessId=None):
        self.uri = uri
        self.payload = payload
        if businessId is not None:
            self.user_ = config.getUserForBusiness(businessId)
            self.pass_ = config.getPasswordForBusiness(businessId)
        else:
            self.user_ = user_
            self.pass_ = pass_
        
    def setBusinessId(self, businessId):
        self.businessId = businessId
        self.user_ = config.getUserForBusiness(businessId)
        self.pass_ = config.getPasswordForBusiness(businessId)
        
    def getBusinessId(self):
        return self.businessId
    
    def execute(self):
        self.login()
        if self.payload != None:
            return self.requestPost()
        else:
            return self.requestGet()
        
        
    def login(self):
        url = uri_+'/auth/login/'
        payload = {
            'username': self.user_,
            'password': self.pass_
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
