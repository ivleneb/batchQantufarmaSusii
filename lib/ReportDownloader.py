import requests
import time

import json
import sys
sys.path.append(r'../')
from lib.QantuConfiguration import QantuConfiguration

class ReportDownloader:
    def __init__(self, reportName, reportCode, headers, init, end, category=None, businessId=None):
        self.rname = reportName
        self.code = reportCode
        self.repHeaders = headers
        self.initDate = init
        self.endDate = end
        # credentials
        config = QantuConfiguration()
        self.uri_ = config.uri_
        if businessId != None:
            self.businessId = businessId
            self.user_ = config.getUserForBusiness(businessId)
            self.pass_ = config.getPasswordForBusiness(businessId)
        else:
            self.businessId = config.business_
            self.user_ = config.user_
            self.pass_ = config.pass_

        if self.code == 'export_products':
            if category == None:
                self.queryParams =  {"package__isnull":'true',
                                 "ordering":"-pk",
                                 "page":1,
                                 "business":self.businessId
                                 }
            else:
                self.queryParams =  {"package__isnull":'true',
                                 "ordering":"-pk",
                                 "business_category__name__icontains":category,
                                 "page":1,
                                 "business":self.businessId
                                 }
        elif self.code == 'export_sales_per_product':
            self.queryParams =  {
                "business": self.businessId,
                "date__gte": self.initDate+"T05:00:00.000Z",
                "date__lte": self.endDate+"T04:59:59.999Z",
                "page": 1
            }
        elif self.code == 'export_packages':
            self.queryParams =  {
                                 "page":1,
                                 "business":self.businessId
                                 }

        elif self.code == 'export_petty_cash_movements':
            self.queryParams =  {
                "business": self.businessId,
                "date__gte": self.initDate+"T05:00:00.000Z",
                "date__lte": self.endDate+"T04:59:59.999Z",
                "page": 1,
                "type": "1"
            }
        elif self.code == 'export_payments_expenses':
            self.queryParams =  {
                "business": self.businessId,
                "date__gte": self.initDate+"T05:00:00.000Z",
                "date__lte": self.endDate+"T04:59:59.999Z",
                "page": 1
            }
        elif self.code == 'export_sales':
            self.queryParams = {
                "page": 1
                }
        
    def execute(self):
        self.login()
        self.requestReport()
        time.sleep(11)
        if self.downloadReport():
            return self.reportName
        else:
            return ""
        
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
        
    def requestReport(self):
        url2 = self.uri_+'/v1/stats/requested-reports/'
        payload2 = {
            "format":"xlsx",
            "from_date":self.initDate+"T04:11:58.791Z",
            "to_date":self.endDate+"T04:59:59.999Z",
            "headers": self.repHeaders,
            "report_code":self.code,
            "business":self.businessId,
            "requested_by":9663,
            "name":self.rname,
            "query_params":self.queryParams
        }

        r = requests.post(url2, headers=self.headers, json=payload2)
        j = r.json()
        print(f"Status Code: {r.status_code}, Response: {r.json()}")
        self.reportId = j['id']
        self.reportName = j['name']

    def downloadReport(self):
        url3 = self.uri_+'/v1/stats/requested-reports/?business='+str(self.businessId)
        r = requests.get(url3, headers=self.headers)
        j = r.json()
        print(f"Status Code: {r.status_code}, Response: {r.json()}")
        
        if not 'results' in j:
            return False
        
        for obj in j['results']:
            if obj['id']==self.reportId:
                response = requests.get(obj['file'])
                open(self.reportName, "wb").write(response.content)
                print("File donwloaded!")
                return True
        return False
