import sys #, os
sys.path.append(r'../')
from lib.QantuProduct import QantuProduct
from lib.QantuProductMerger import QantuProductMerger
from datetime import datetime
from lib.SusiiProductLoader import SusiiProductLoader
import json
import pandas

otherBusiness = 8132
lazaro = 8132
cobian = 5053
# Read JSON file
with open('../lib/cfg.json', 'r', encoding='utf-8') as file:
    cfgData = json.load(file)
    business_ = cfgData["businessId"]
    if business_ == cobian:
        otherBusiness = lazaro
    elif business_ == lazaro:
        otherBusiness = cobian

def generateReport(moveList):
    cols3 = [ "CÓDIGO", "NOMBRE", "CANTIDAD"]
    move_df = pandas.DataFrame(moveList, columns = cols3)
    now = datetime.now().strftime("%Y%m%d")
    excel_name = str(business_)+'_ToMoveFrom'+str(otherBusiness)+'_'+now+'.xlsx'
    with pandas.ExcelWriter(excel_name) as excel_writer:
        move_df.to_excel(excel_writer, index=False)

def run():
    loader = SusiiProductLoader(business_)

    # load products from q1
    productDict:dict[str, QantuProduct] = loader.downloadProducts(downloadSaleData=True)
    if not productDict:
        print("Fail to downloadProducts.")
        sys.exit(2)

    productDict = QantuProductMerger.combineProducts(productDict)

    # load products from q2
    loader.setBusinessId(otherBusiness)
    productDictOther:dict[str, QantuProduct] = loader.downloadProducts()
    if not productDictOther:
        print("Fail to downloadProducts from OTHER.")
        sys.exit(3)
    
    productDictOther = QantuProductMerger.combineProducts(productDictOther)
    
    # for p1 in products of q1
    moveList = []
    for prodCode in productDict:
        prod = productDict[prodCode]
        active_days = prod.getActiveDays()
        if active_days==0:
            print("Active days is 0, default to 1")
            active_days=1
        stock = prod.getStock()
        daily_mean = prod.getSoldUnits()/active_days
        requestQtty = 30*daily_mean - stock
        # if p1.pedirValue>=0 and stock of p1 in q1 is 0
        if requestQtty > 0 and stock == 0:
            print("Prod["+prod.getName()+"] require units.")
            # if p1 exist in q2 and p1 stock in q2 >= unitsBlister
            if prodCode in productDictOther:
                # agregar a lista de traslado 1 blister
                prod2 = productDictOther[prodCode]
                if prod2.getCategory()=='MEDICAMENTOS':
                    if prod2.getUnitsBlister()>0 and prod2.getStock()>prod2.getUnitsBlister() and prod2.getStock()-prod2.getUnitsBlister()>0:
                        print("Trasladar!")
                        moveList.append([prod.getCode(), prod.getName(), prod2.getUnitsBlister()])
                    elif prod2.getUnitsCaja()>0 and prod2.getStock()>prod2.getUnitsCaja() and prod2.getStock()-prod2.getUnitsCaja()>0:
                        print("Trasladar!")
                        moveList.append([prod.getCode(), prod.getName(), prod2.getUnitsCaja()])
                    else:
                        print("Check units blister or units cja.")
                elif prod2.getCategory()!='MEDICAMENTOS' and prod2.getStock()>1:
                    print("Trasladar!")
                    moveList.append([prod.getCode(), prod.getName(), 1])
                else:
                    print("There is not enough stock.")
            else:
                print("Prod["+prod.getName()+"] NOT in OTHER store.")

    
    generateReport(moveList)

run()