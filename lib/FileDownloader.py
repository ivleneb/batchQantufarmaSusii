import requests
import time

import json
import sys
sys.path.append(r'../')
from lib.QantuConfiguration import QantuConfiguration

class FileDownloader:
    def __init__(self, init, end):
        self.initDate = init
        self.endDate = end
        self.purchases = {}
        config = QantuConfiguration()
        # credentials
        self.business_ = config.business_
        self.user_ = config.user_
        self.pass_ = config.pass_
        self.uri_ = config.uri_
        
    def execute(self):
        self.login()
        self.listPurchases()
        time.sleep(10)
        count=0
        for number, purchase_id in self.purchases.items():
            self.download(number, purchase_id)
            count+=1
        print("total files downloaded "+str(count))
        return True
        
    def login(self):
        url = self.uri_+'/auth/login/'
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
        
    def listPurchases(self):
        for i in range(1,4):
            url2 = self.uri_+"/purchases/purchases/" \
                "?page={0}&business="+str(business_)+"&date__gte={1}T05:00:00.000Z&"\
                "date__lte={2}T04:59:59.999Z".format(i, self.initDate, self.endDate)
            
            r = requests.get(url2, headers=self.headers)
            j = r.json()
            
            if not 'results' in j:
                return
            
            for res in j['results']:
                print("document number: {0}, id: {1}".format(res['document_number'], res['id']))
                self.purchases[res['number']]=res['id']
            
        

    def download(self, number, purchase):
        url3 = self.uri_+'/v1/purchases/purchases/'+str(purchase)+'/?business='+str(self.business_)
        r = requests.get(url3, headers=self.headers)
        j = r.json()
        print(f"Status Code: {r.status_code}, Response: {r.json()}")
        
        if not 'receipt_file' in j:
            return False
        
        if j['receipt_file'] is None:
            return False
        
        response = requests.get(j['receipt_file'])
        filename = j['receipt_file'].split("/")
        filename = filename[-1]
        print("storing "+filename)
        print("purchase number: "+str(number))
        open(filename, "wb").write(response.content)
        print("File donwloaded!")
        return True
