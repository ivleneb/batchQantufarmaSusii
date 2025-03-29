import requests
import time

import json

# Read JSON file
with open('../lib/cfg.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
    user_ = data["user"]
    pass_ = data["password"]
    uri_ = data["uri"]

class ReportDownloader:
    def __init__(self, reportName, reportCode, headers, init, end, category=None):
        self.rname = reportName
        self.code = reportCode
        self.repHeaders = headers
        self.initDate = init
        self.endDate = end
        if self.code == 'export_products':
            if category == None:
                self.queryParams =  {"package__isnull":'true',
                                 "ordering":"-pk",
                                 "page":1,
                                 "business":5053
                                 }
            else:
                self.queryParams =  {"package__isnull":'true',
                                 "ordering":"-pk",
                                 "business_category__name__icontains":category,
                                 "page":1,
                                 "business":5053
                                 }
        elif self.code == 'export_sales_per_product':
            self.queryParams =  {
                "business": 5053,
                "date__gte": self.initDate+"T05:00:00.000Z",
                "date__lte": self.endDate+"T04:59:59.999Z",
                "page": 1
            }
        elif self.code == 'export_packages':
            self.queryParams =  {
                                 "page":1,
                                 "business":5053
                                 }

        elif self.code == 'export_petty_cash_movements':
            self.queryParams =  {
                "business": 5053,
                "date__gte": self.initDate+"T05:00:00.000Z",
                "date__lte": self.endDate+"T04:59:59.999Z",
                "page": 1,
                "type": "1"
            }
        elif self.code == 'export_payments_expenses':
            self.queryParams =  {
                "business": 5053,
                "date__gte": self.initDate+"T05:00:00.000Z",
                "date__lte": self.endDate+"T04:59:59.999Z",
                "page": 1
            }
        
    def execute(self):
        self.login()
        self.requestReport()
        time.sleep(10)
        if self.downloadReport():
            return self.reportName
        else:
            return ""
        
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
        
    def requestReport(self):
        url2 = uri_+'/v1/stats/requested-reports/'
        payload2 = {
            "format":"xlsx",
            "from_date":self.initDate+"T04:11:58.791Z",
            "to_date":self.endDate+"T04:59:59.999Z",
            "headers": self.repHeaders,
            "report_code":self.code,
            "business":5053,
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
        url3 = uri_+'/v1/stats/requested-reports/?business=5053'
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
