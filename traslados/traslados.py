import sys
sys.path.append(r'../')
from lib.QantuProduct import QantuProduct
from lib.QantuMergedProduct import QantuMergedProduct
from lib.QantuProductMerger import QantuProductMerger
from lib.QantuConfiguration import QantuConfiguration
from datetime import datetime
from lib.SusiiProductLoader import SusiiProductLoader
from lib.BatchUtils import BatchUtils
import pandas

otherBusiness = 8132
lazaro = 8132
cobian = 5053
# load configuration
config = QantuConfiguration()
# business id
business_ = config.business_
if business_ == cobian:
    otherBusiness = lazaro
elif business_ == lazaro:
    otherBusiness = cobian
else:
    print("FATAL invalid business "+str(business_))
    sys.exit(1)

def generateReport(moveList):
    cols3 = [ "CÓDIGO", "NOMBRE", "CANTIDAD"]
    move_df = pandas.DataFrame(moveList, columns = cols3)
    now = datetime.now().strftime("%Y%m%d")
    excel_name = str(business_)+'_ToMoveFrom'+str(otherBusiness)+'_'+now+'.xlsx'
    out_path = './out'
    BatchUtils.crear_carpeta_si_no_existe(out_path)
    fullpath = out_path+'/'+excel_name
    with pandas.ExcelWriter(fullpath) as excel_writer:
        move_df.to_excel(excel_writer, index=False)

def run():
    loader = SusiiProductLoader(business_)

    # load products from q1
    productDict:dict[str, QantuProduct] = loader.downloadProducts(downloadSaleData=True, includeDisable=True)
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
        if  prod.isDisable():
            continue
        
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
                        moveList.append([prod.getCode(), prod.getMergedName(), prod2.getUnitsBlister()])
                    elif prod2.getUnitsCaja()>0 and prod2.getStock()>prod2.getUnitsCaja() and prod2.getStock()-prod2.getUnitsCaja()>0:
                        print("Trasladar!")
                        moveList.append([prod.getCode(), prod.getMergedName(), prod2.getUnitsCaja()])
                    else:
                        print("Prod ["+prod2.getName()+"] Check units blister or units cja.")
                elif prod2.getCategory()!='MEDICAMENTOS' and prod2.getStock()>1:
                    print("Trasladar!")
                    moveList.append([prod.getCode(), prod.getName(), 1])
                else:
                    print("There is not enough stock.")
            else:
                print("Prod["+prod.getName()+"] NOT in OTHER store.")

    print("\n\nPRODUCTOS NUEVOS-------------------------------------------------------------------")
    for prodCode in productDictOther:
        if not prodCode in productDict:
            prod2 = productDictOther[prodCode]
            # si es combinado revisar si alguno de los elementos existe en el destino
            if isinstance(prod2, QantuMergedProduct):
                skip = False
                for codeInner in prod2.products:
                    try:
                        print("Element ["+codeInner+"]"+prod2.products[codeInner].getName())
                    except TypeError:
                        print(type(codeInner))
                        print(codeInner.__class__)
                    if codeInner in productDict:
                        print("Element ["+codeInner+"]"+prod2.products[codeInner].getName()+" exists in destiny DB.")
                        skip = True
                        break
                if skip:
                    continue
            # si no es combinado revisar si puede existir en algun combinado en el destino
            elif prod2.functionalCode() in productDict:
                print("Element ["+prod2.getCode()+"]"+prod2.getName()+" has equivalent in destiny DB.")
                continue
            else:
                skip = False
                for prodCodeX in productDict:
                    prodX = productDict[prodCodeX]
                    words = ["PAPEL", "PAÑUELO", "SACHET", "DESODORANTE", "REGALO"]
                    if prod2.functionalCode() == prodX.functionalCode():
                        print("Element ["+prod2.getCode()+"]"+prod2.getName()+" has equivalent in destiny DB ("+prodX.getCode()+").")
                        skip = True
                        break
                    elif prod2.getName()==prodX.getName():
                        print("Element ["+prod2.getCode()+"]"+prod2.getName()+" has equivalent in destiny DB ("+prodX.getName()+").")
                        skip = True
                        break
                    elif any(w in prod2.getName() for w in words):
                        print("Element ["+prod2.getCode()+"]"+prod2.getName()+" has banned from traslados")
                        skip = True
                        break
                if skip:
                    continue
            if prod2.getCategory()=='MEDICAMENTOS':
                # agregar a lista de traslado 1 blister
                if prod2.getUnitsBlister()>0 and prod2.getStock()>prod2.getUnitsBlister():
                    print("PROD ["+prod2.getCode()+"]"+prod2.getName()+" no existe en "+str(business_))
                    if isinstance(prod2, QantuMergedProduct):
                        print("IS QantuMergedProduct "+prod2.getCode())
                    print("Trasladar!")
                    moveList.append([prod2.getCode(), prod2.getMergedName(), prod2.getUnitsBlister()])
                elif prod2.getUnitsCaja()>0 and prod2.getStock()>prod2.getUnitsCaja():
                    print("PROD "+prod2.getName()+" no existe en "+str(business_))
                    if isinstance(prod2, QantuMergedProduct):
                        print("IS QantuMergedProduct "+prod2.getCode())
                    print("Trasladar!")
                    moveList.append([prod2.getCode(), prod2.getMergedName(), prod2.getUnitsCaja()])
                else:
                    print("Prod ["+prod2.getName()+"] Check units blister or units cja.")
            elif prod2.getCategory()!='MEDICAMENTOS' and prod2.getStock()>1:
                print("PROD "+prod2.getName()+" no existe en "+str(business_))
                print("Trasladar!")
                if isinstance(prod2, QantuMergedProduct):
                    print("IS QantuMergedProduct "+prod2.getCode())
                moveList.append([prod2.getCode(), prod2.getName(), 1])
            else:
                print("There is not enough stock.")
        
    
    generateReport(moveList)

run()