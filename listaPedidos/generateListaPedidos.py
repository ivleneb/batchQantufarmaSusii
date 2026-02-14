import sys #, os
sys.path.append(r'../')
from lib.QantuProduct import QantuProduct
from lib.QantuPackage import QantuPackage
from lib.QantuConfiguration import QantuConfiguration
from lib.SusiiProductLoader import SusiiProductLoader
from lib.QantuProductMerger import QantuProductMerger
import pandas
from datetime import datetime
from datetime import timedelta
import re

config = QantuConfiguration()
# Pedir stock para NBR_DAYS dias (default 30)
NBR_DAYS = config.NBR_DAYS 
# Poner a 0 los stock de todos los productos
stock_0 = config.stock_0
# business id
business_ = config.business_

rowProv=1
colCOD = 'A'
colNOMBRE = 'B'
colCATEGORIA = 'C'
colPA = 'D'
colSTOCK = 'E'
colBRAND = 'F'
colPRVDOR = 'G'
colCOSTO = 'H'
colPRECIO = 'I'
colVENTAS = 'J'
colPER = 'K'
colBLI = 'L'
colCJA = 'M'
colPEDIR = 'N'
colFINAL = 'O'
colCOSTOCJA = 'P'
colTOTAL = 'Q'


def isFF(ls, name):
    for l in ls:
        if l in name:
            return True
    return False

def remove_lab(input_string):
    s =re.sub(r'\[.*?\]', '', input_string)
    return s.strip()

def createDataProvList(prov, cont):
    data = []
    filt = '=FILTER(Productos!{ColC}2:{ColT}{num},Productos!{colE}2:{colE}{num}="{pr}")'.format(
        ColC = colCOD,
        ColT = colTOTAL,
        num = cont,
        pr = prov,
        colE = colPRVDOR
        )
    l = [filt, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
    data.append(l)
    return data

def medsCriteria(prod, pedirVal, perVal):
    final = '=0'
    
    if pedirVal<0.5:
        return final
    
    cja = prod.getUnitsCaja()

    if cja==0 and isFF(["TUB", "FCO"], prod.getName()):
        print("DEFAULT for TUB or FCO is 1 "+prod.getName())
        cja = 1
    elif cja==0 and isFF(["TAB", "CAP"], prod.getName()):
        print("DEFAULT for TAB or CAP is 30 "+prod.getName())
        cja = 30

    if cja == prod.getCantidad():
        cja = 1

    flag = False
    for i in range(20):
        if cja*(i+0.25)<pedirVal and cja*(i+1.25)>pedirVal:
            final = '={val}'.format(val=i+1)
            flag = True
            break

    if not flag and perVal>0.5:
        final = '={val}'.format(val=1)
    
    return final

def bellezaCriteria(prod, pedirVal, perVal):
    final = '=0'
    
    if prod.getStock()<=0 and pedirVal<0.25:
        return final
    
    cja = prod.getUnitsCaja()
    if cja==0:
        print("DEFAULT for OTHERS CAT is 1 "+prod.getName())
        cja = 1

    flag = False
    for i in range(20):
        if cja*(i+0.25)<pedirVal and cja*(i+1.25)>pedirVal:
            final = '={val}'.format(val=i+1)
            flag = True
            break

    if not flag and perVal>=0.25:
        final = '={val}'.format(val=1)
    
    return final

def defaultCriteria(prod, pedirVal, perVal):
    final = '=0'
    
    if prod.getStock()<=0 and pedirVal<0.25:
        return final
    
    cja = prod.getUnitsCaja()
    if cja==0:
        print("DEFAULT for OTHERS CAT is 1 "+prod.getName())
        cja = 1

    flag = False
    for i in range(20):
        if cja*(i+0.25)<pedirVal and cja*(i+1.25)>pedirVal:
            final = '={val}'.format(val=i+1)
            flag = True
            break

    if not flag and perVal>=0.25:
        final = '={val}'.format(val=1)
    
    return final

def createDataList(prodDict, providers):
    data = []
    count = 0

    for prod in prodDict.values():
        
        if stock_0:
            prod.setStock(0)
        
        count = count + 1
        pedir = '=({dys}*{colV}{rowV}/{n})-{colS}{rowS}'.format(
            dys=NBR_DAYS, n=prod.getActiveDays(),
            colV=colVENTAS, rowV=count+1,
            colS=colSTOCK, rowS=count+1)
        
        per = '= {colP}{rowP}/ABS({colS}{rowS})'.format(
            colP=colPEDIR, rowP=count+1,
            colS=colSTOCK, rowS=count+1)
        
        if prod.getStock()==0:
            per = '=100'
            
        active_days = prod.getActiveDays()
        if active_days==0:
            active_days=1
        
        daily_mean = prod.getSoldUnits()/active_days
        
        pedirVal = (NBR_DAYS*daily_mean-prod.getStock())
        if active_days < 30:
            pedirVal = (active_days*daily_mean-prod.getStock())
            print("LESS THAN 30 days "+prod.getName())
            pedir = '={pedirValue}'.format(pedirValue=pedirVal) 
        
        
        perVal = 0
        if prod.getStock()!=0:
            perVal = pedirVal/prod.getStock()
        else:
            perVal = 1000
        
        final = '0'
        if prod.getCategory() == 'MEDICAMENTOS':
            final = medsCriteria(prod, pedirVal, perVal)
        elif prod.getCategory() == 'BELLEZA':
            final = bellezaCriteria(prod, pedirVal, perVal)
        else:
            final = defaultCriteria(prod, pedirVal, perVal)

        priceCja =  '={colCostUni}{rowP}*{colCaja}{rowP}'.format(
            colCostUni=colCOSTO,
            colCaja=colCJA,
            rowP=count+1)
        
        monto =  '={colCostUni}{rowP}*{colCaja}{rowP}*{colF}{rowP}'.format(
            colCostUni=colCOSTO,
            colCaja=colCJA,
            colF=colFINAL,
            rowP=count+1)
        
        l=[]
        
        #pName = prod.getName()
        #if prod.getUnitsCaja()!=0:
        #    pName = prod.getName()+" X "+str(int(prod.getUnitsCaja()))
        
        if prod.getCategory() == 'MEDICAMENTOS':
            l = [prod.getCode(), prod.getMergedName(), prod.getCategory(), prod.getPrincipioActivo(),
                     prod.getStock(), prod.getBrand(), prod.getLastProvider(),
                     prod.getLastCost(), prod.getPrice(), prod.getSoldUnits(), per, prod.getUnitsBlister(), prod.getUnitsCaja(),
                     pedir, final, priceCja, monto]
        else:
            l = [prod.getCode(), prod.getMergedName(), prod.getCategory(), '',
                     prod.getStock(), prod.getBrand(), prod.getLastProvider(),
                     prod.getLastCost(), prod.getPrice(), prod.getSoldUnits(), per, 0, prod.getUnitsCaja(),
                     pedir, final, priceCja, monto]

        data.append(l)
        
        lastProvider = prod.getLastProvider()
        if lastProvider == None or isinstance(lastProvider, float):
            lastProvider = ""    
        
        if not lastProvider in providers:
            providers.append(lastProvider)
        
    return data

def run():
    providers:list[str] = []
    print("------------------------ INIT ---------------------------")

    now = (datetime.now()+ timedelta(days=1)).strftime("%Y-%m-%d")
    
    loader = SusiiProductLoader(business_)

    # load products from q1
    prodDict:dict[str, QantuProduct] = loader.downloadProducts(downloadSaleData=True)
    if not prodDict:
        print("Fail to downloadProducts.")
        sys.exit(2)

    # load products from q1
    packDict:dict[str, QantuPackage] = loader.downloadPackages(downloadSaleData=True)
    if not packDict:
        print("Fail to downloadPackages.")
        sys.exit(3)

    # Incresase sold unit according to package
    print("First product filter")
    for pack in packDict.values():
        for packprodCode, qty in pack.getItems().items():
            if packprodCode in prodDict.keys():
                prodDict[packprodCode].addSoldUnits(qty*pack.getSoldUnits())
                #if prodDict[packprodCode].

    prodDict = QantuProductMerger.combineProducts(prodDict)

    dataOut = createDataList(prodDict, providers)
    #dataMeds = createDataList(medsDict)
    #dataOther = createDataList(otherDict)
    #countMeds = len(dataMeds)
    #countOther =len(dataOther)
    countProds = len(dataOut)

    cols = ['COD', 'NOMBRE', 'CATEGORIA', 'PA', 'STOCK', 'BRAND', 'PRVDOR', 'COSTO',
            'PRECIO', 'VENTAS', 'PER', 'BLI', 'CJA', 'PEDIR', 'FINAL', 'COSTOCJA', 'MONTO']
    #outMed_df = pandas.DataFrame(dataMeds, columns = cols)
    #outOther_df = pandas.DataFrame(dataOther, columns = cols)
    out_df = pandas.DataFrame(dataOut, columns = cols)

    now = datetime.now().strftime("%Y%m%d_%H%M")
    excel_name = str(business_)+'_ListaPedidos_'+now+'.xlsx'

    with pandas.ExcelWriter(excel_name) as excel_writer:
        out_df.to_excel(excel_writer, sheet_name='Productos', index=False)
        #outMed_df.to_excel(excel_writer, sheet_name='Medicamentos', index=False)
        #outOther_df.to_excel(excel_writer, sheet_name='Otros', index=False)
        for prov in providers:
            dataProvList = createDataProvList(prov, countProds)
            prov_df = pandas.DataFrame(dataProvList, columns = cols)
            prov_df.to_excel(excel_writer, sheet_name='Lista_'+prov, index=False)
            
    print("------------------------  END ---------------------------")


run()