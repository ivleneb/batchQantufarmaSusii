import sys
sys.path.append(r'../')
from lib.QantuPackage import QantuPackage
from lib.QantuProduct import QantuProduct
from lib.QantuProductMerger import QantuProductMerger
from lib.SusiiProductLoader import SusiiProductLoader
from lib.QantuConfiguration import QantuConfiguration
import pandas
from datetime import datetime
from datetime import timedelta
import re

config = QantuConfiguration()
# Pedir stock para NBR_DAYS dias (default 30)
NBR_DAYS = config.NBR_DAYS 
# business id
business_ = config.business_

providers = ['DROGE', 'V&G', 'DPERU', 'EURO', 'INKAF',  'LIMAC',
        'CBC', 'VEGA', 'AGREEN']
colProvI = 'L'
colProvF = chr(ord(colProvI)+len(providers)-1)
rowProv=1
colProv=ord(colProvI)-ord('A')
colFinal = 'K'
colVenta = 'H'
colStock = 'C'
colPedir = 'J'
colElegi = 'U'

def remove_lab(input_string):
    return re.sub(r'\[.*?\]', '', input_string)

def createDataProvList(prov, cont):
    data = []
    filt = '=FILTER(Medicamentos!A2:U{num},Medicamentos!{colE}2:{colE}{num}="{pr}")'.format(
        num = cont,
        pr = prov,
        colE = colElegi
        )
    prs = []
    for p in providers:
        prs.append('')
    l = [filt, '', '', '', '', '', '', '', '', '', ''] + prs + ['', '']
    data.append(l)
    return data

def createDataList(prodDict):
    data = []
    count = 0

    for prod in prodDict.values():
        count = count + 1
        pedir = '=({dys}*{colV}{rowV}/{n})-{colS}{rowS}'.format(
            dys=NBR_DAYS, n=prod.getActiveDays(),
            colV=colVenta, rowV=count+1,
            colS=colStock, rowS=count+1)
        
        per = '= {colP}{rowP}/ABS({colS}{rowS})'.format(
            colP=colPedir, rowP=count+1,
            colS=colStock, rowS=count+1)
        
        if prod.getStock()==0:
            per = '=100'
            
        active_days = prod.getActiveDays()
        if active_days==0:
            active_days=1
        
        daily_mean = prod.getSoldUnits()/active_days
        pedirVal = NBR_DAYS*daily_mean

        if prod.getMinStock() > prod.getStock():
            pV = prod.getMinStock() - prod.getStock()
            if pV>pedirVal:
                pedir = '={val}'.format(val=pV)
        final = 0
        prs = []
        for p in providers:
            prs.append('')

        elegido = '''=INDIRECT(ADDRESS({rowPr}, {colPr}+MATCH(
                MIN({colPrI}{rowP}:{colPrF}{rowP}),
                {colPrI}{rowP}:{colPrF}{rowP},0
                )))'''.format(
            rowPr=rowProv, colPr=colProv,
            colPrI=colProvI, colPrF=colProvF,
            rowP=count+1)
        monto =  '=MIN({colPrI}{rowP}:{colPrF}{rowP})*{colF}{rowP}'.format(
            colPrI=colProvI, colPrF=colProvF,
            colF=colFinal, rowP=count+1)
        l = [prod.getCode(), remove_lab(prod.getName()), prod.getStock(), prod.getBrand(), prod.getLastProvider(),
                     prod.getLastCost(), prod.getPrice(), prod.getSoldUnits(), per,
                     pedir, final]
        l = l + prs + [re.sub(r'\s+', ' ', elegido.replace('\n', '')), monto, prod.getOtc()]
        data.append(l)
        
    return data

def run():
    
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

   
    prodDict = QantuProductMerger.combineProducts(prodDict)

    medsDict = {}
    otherDict = {}
    for key, prod in prodDict.items():
        if prod.getCategory()=='MEDICAMENTOS':
            medsDict[key]=prod
        else:
            otherDict[key]=prod

    dataMeds = createDataList(medsDict)
    dataOther = createDataList(otherDict)

    cols = ['COD', 'NOMBRE', 'STOCK', 'BRAND', 'PRVDOR', 'COSTO',
            'PRECIO', 'VENTAS', 'PER', 'PEDIR', 'FINAL']
    cols = cols + providers + ['ELEGIDO', 'MONTO', 'OTC']
    outMed_df = pandas.DataFrame(dataMeds, columns = cols)
    outOther_df = pandas.DataFrame(dataOther, columns = cols)

    now = datetime.now().strftime("%Y%m%d")
    excel_name = 'ListaPedidos_'+now+'.xlsx'

    with pandas.ExcelWriter(excel_name) as excel_writer:
        outMed_df.to_excel(excel_writer, sheet_name='Medicamentos', index=False)
        outOther_df.to_excel(excel_writer, sheet_name='Otros', index=False)
        
run()
