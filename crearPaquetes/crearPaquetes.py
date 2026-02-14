import sys
sys.path.append(r'../')
#from lib.libclass import *
from lib.QantuProduct import QantuProduct
from lib.QantuPackage import QantuPackage
#from lib.QantuMedicine import QantuMedicine
#from lib.QantuGalenico import QantuGalenico
#from lib.QantuDevice import QantuDevice
#from lib.QantuGeneral import QantuGeneral
from lib.PriceManager import PriceManager
#from lib.ReportDownloader import ReportDownloader
from lib.QantuConfiguration import QantuConfiguration
from lib.SusiiProductLoader import SusiiProductLoader
#from lib.QantuProductMerger import QantuProductMerger
import pandas
from datetime import datetime
#import json

config = QantuConfiguration()
# business id
business_ = config.business_

def checkPackType(pack, prod):
    pNameLow = pack.getName().lower()
    if pNameLow.startswith('blister'):
        cantidadItemBlis = int(pack.items[prod.getCode()])
        if int(prod.getUnitsBlister())!= cantidadItemBlis:
            print("WARNING. UnitsBlister different from CANTIDAD (ITEM) for "+prod.getName())
    elif pNameLow.startswith('cja'):
        cantidadItemCja = int(pack.items[prod.getCode()])
        if int(prod.getUnitsCaja())!= cantidadItemCja:
            print("WARNING. UnitsCaja different from CANTIDAD (ITEM) for "+prod.getName())
    else:
        print("WARNING invalid pack type ["+pack.getName()+"]") 

def createPackageBlister(prod):
    cantidadItemBlis = int(prod.getUnitsBlister())
    #packPrice = round(prod.getPrice()*cantidadItemBlis*0.7, 1)
    price = PriceManager.computeProductBlisterPrice(prod)
    if price is None:
        print("ERROR Failed to compute blister price for prod "+prod.getName())
        return []
    
    packName = "Blister "+prod.getName()+"X"+str(cantidadItemBlis)
    packPrice = price.getValue()
    ls = [ prod.getCode()+"BLI"+str(cantidadItemBlis), packName, "", "UNIDAD",
        packPrice,  prod.getCategory(), prod.getCode(), prod.getName(),
        "", prod.getUnidad(), prod.getPrice(), cantidadItemBlis
    ]
    print("NUEVO BLISTER: ")
    print(ls)
    return ls

def createPackageCja(prod):
    cantidadItemCja = int(prod.getUnitsCaja())
    #packPrice = round(prod.getPrice()*cantidadItemCja*0.5, 1)
    price = PriceManager.computeProductCajaPrice(prod)
    if price is None:
        print("ERROR Failed to compute caja price for prod "+prod.getName())
        return []
    
    packName = "Cja "+prod.getName()+"X"+str(cantidadItemCja)
    packPrice = price.getValue()
    ls = [ prod.getCode()+"CJA"+str(cantidadItemCja), packName, "", "UNIDAD",
        packPrice,  prod.getCategory(), prod.getCode(), prod.getName(),
        "", prod.getUnidad(), prod.getPrice(), cantidadItemCja
    ]
    print("NUEVA CJA: ")
    print(ls)
    return ls

def nameHas(prod, text):
    if text.upper() in prod.upper():
        return True
    else:
        return False

def createDataListToImportPack(prodDict, packDict):
    data = []
    count = 0

    for prod in prodDict.values():
        count = count + 1
        
        if prod.getStock()<=0:
            print("Product["+prod.getName()+"] hasn't stock.")
            continue

        #if prod.getCategory()=='MEDICAMENTOS' and prod.isGenerico():
        if prod.getCategory()=='MEDICAMENTOS':
            if prod.getFF() in ['TAB', 'TAB_REC', 'SOB_2_TAB_REC', 'CJA_1_TAB_REC', 'CAP']:
                hasPack=False
                hasCja = False
                hasBlister = False
                for key, pack in packDict.items():
                    if prod.getCode() in pack.itemsObj :
                        if len(pack.itemsObj)==1:
                            hasPack=True
                            if nameHas(pack.getName(), 'Cja'):
                                hasCja = True
                            if nameHas(pack.getName(), 'Blister'):
                                hasBlister = True
                            print("PROD["+prod.getName()+"] already has pack["+pack.getName()+"].")
                            # check for type
                            checkPackType(pack, prod)
                        else:
                            print("WARNING PACK["+pack.getName()+"] has more than 1 item.")
                # No pack found
                cantidadItemBlis = int(prod.getUnitsBlister())
                cantidadItemCja = int(prod.getUnitsCaja())
                if not hasPack:
                    if 'SOB' in prod.getFF().upper():
                        print("WARNING prod["+prod.getName()+"] FF is SOB.")
                    else:
                        print("NO_PACK PROD["+prod.getName()+"] hasn't pack. Create!")
                        # crear blister  
                        if cantidadItemBlis == 1:
                            print("WARNING prod["+prod.getName()+"] has unitsBlister["+str(cantidadItemBlis)+"]")
                        else:
                            ls = createPackageBlister(prod)
                            if len(ls)!=0:
                                data.append(ls)
                    
                    # crear cja
                    if cantidadItemCja == 1:
                        print("WARNING prod["+prod.getName()+"] has unitsCja["+str(cantidadItemCja)+"]")
                    elif cantidadItemCja == cantidadItemBlis:
                        continue
                    else:
                        ls = createPackageCja(prod) 
                        if len(ls)!=0:
                            data.append(ls)
                else:         
                    if not hasCja:
                        print("NO_PACK_CJA PROD["+prod.getName()+"] hasn't pack CJA. Create!")
                        # crear cja
                        if cantidadItemCja == 1:
                            print("WARNING prod["+prod.getName()+"] has unitsCja["+str(cantidadItemCja)+"]")
                        elif cantidadItemCja == cantidadItemBlis:
                            continue
                        else:
                            ls = createPackageCja(prod)
                            if len(ls)!=0:
                                data.append(ls)
                    
                    if not hasBlister and not ('SOB' in prod.getFF().upper()):
                        print("NO_PACK_BLISTER PROD["+prod.getName()+"] hasn't pack BLISTER. Create!")
                        # crear blister
                        if cantidadItemBlis == 1:
                            print("WARNING prod["+prod.getName()+"] has unitsBlister["+str(cantidadItemBlis)+"]")
                        else:
                            ls = createPackageBlister(prod)
                            if len(ls)!=0:
                                data.append(ls)
            else:
                continue
        else:
            continue
    return data  

def run():
    #today = datetime.now().strftime("%Y-%m-%d")

    loader = SusiiProductLoader(business_)

    # load products from q1
    productsDict:dict[str, QantuProduct] = loader.downloadProducts(downloadSaleData=True)
    if not productsDict:
        print("Fail to downloadProducts.")
        sys.exit(2)

    # load products from q1
    packageDict:dict[str, QantuPackage] = loader.downloadPackages(downloadSaleData=True)
    if not packageDict:
        print("Fail to downloadPackages.")
        sys.exit(3)

    medsDict = {}
    otherDict = {}
    for key, prod in productsDict.items():
        if prod.getCategory()=='MEDICAMENTOS':
            medsDict[key]=prod
        else:
            otherDict[key]=prod

    #dataMeds = createDataList(medsDict)
    #dataOther = createDataList(otherDict)
    #dataPack = createDataListPack(packDict)

    now = datetime.now().strftime("%Y%m%d")


    cols3 = [ "CÓDIGO", "NOMBRE", "ALIAS", "UNIDAD", "PRECIO DE VENTA", "CATEGORÍA", "CÓDIGO (ITEM)", "NOMBRE (ITEM)",
              "ALIAS (ITEM)", "UNIDAD (ITEM)", "PRECIO DE VENTA (ITEM)", "CANTIDAD (ITEM)"
        ]

    import_pack = createDataListToImportPack(medsDict, packageDict)
    importpk_df = pandas.DataFrame(import_pack, columns = cols3)
    excel_name = str(business_)+'_PriceToImportPack_'+now+'.xlsx'
    with pandas.ExcelWriter(excel_name) as excel_writer:
        importpk_df.to_excel(excel_writer, index=False)



run()