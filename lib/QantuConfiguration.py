import sys
sys.path.append(r'../')
import json

class QantuConfiguration:
    
    # Pedir stock para NBR_DAYS dias (default 30)
    NBR_DAYS=30
    # Poner a 0 los stock de todos los productos
    stock_0 = False
    # bussines id
    business_ = 0
    # credential
    user_ = None
    pass_ = None
    # uri
    uri_ = None
    
    def __init__(self):
        self.dataCfg = None
        # Read JSON file
        with open('../lib/cfg.json', 'r', encoding='utf-8') as file:
            dataCfg = json.load(file)
            QantuConfiguration.business_ = dataCfg["businessId"]
            QantuConfiguration.NBR_DAYS = dataCfg["nbrDays"]
            QantuConfiguration.stock_0 = dataCfg["zeroStock"]
            QantuConfiguration.user_ = dataCfg["credentials"][str(QantuConfiguration.business_)]["user"]
            QantuConfiguration.pass_ = dataCfg["credentials"][str(QantuConfiguration.business_)]["password"]
            QantuConfiguration.uri_ = dataCfg["uri"]
            self.dataCfg = dataCfg
    
    def getUserForBusiness(self, business):
        return self.dataCfg["credentials"][str(business)]["user"]
    
    def getPasswordForBusiness(self, business):
        return self.dataCfg["credentials"][str(business)]["password"]