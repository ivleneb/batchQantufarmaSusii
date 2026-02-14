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
    
    def __init__(self):
        # Read JSON file
        with open('../lib/cfg.json', 'r', encoding='utf-8') as file:
            dataCfg = json.load(file)
            QantuConfiguration.business_ = dataCfg["businessId"]
            QantuConfiguration.NBR_DAYS = dataCfg["nbrDays"]
            QantuConfiguration.stock_0 = dataCfg["zeroStock"]
