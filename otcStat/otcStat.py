import sys, os
sys.path.append(r'../')
from lib.libclass import *
from lib.ReportDownloader import *
import pandas
from datetime import datetime
from datetime import timedelta
import re
import math

# pedir stock para NBR_DAYS dias
NBR_DAYS=30

prodDict = {}
packDict = {}
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

def addSaleData(prod, sale_df):
    sub_df = sale_df.loc[sale_df['CÓDIGO'] == prod.getCode()]
    if len(sub_df)==1:
        row = sub_df.iloc[0]
        # add sale data
        prod.setLastProvider(row['ÚLTIMO PROVEEDOR'])
        #prod.setLastCost(row['ÚLTIMO PRECIO DE COMPRA'])
        #prod.setPrice(row['ACTUAL PRECIO DE VENTA'])
        prod.setSoldUnits(row['CANTIDAD TOTAL'])
    elif len(sub_df)==0:
        if(prod.getActiveDays()>90 and prod.getStock()>0):
            print("Product ["+prod.getName()+"] never sale!")
        prod.setSoldUnits(0)
    else:
        print(sub_df)
        print("Code with multiple products.")
        print("Consider accumulated.")
        lastProv=""
        soldUnits=0
        for i in range(len(sub_df)):
            
            row = sub_df.iloc[i]
            print(row['NOMBRE'])
            lastProv=row['ÚLTIMO PROVEEDOR']
            soldUnits+=row['CANTIDAD TOTAL']
        # add sale data
        prod.setLastProvider(lastProv)
        #prod.setLastCost(row['ÚLTIMO PRECIO DE COMPRA'])
        #prod.setPrice(row['ACTUAL PRECIO DE VENTA'])
        prod.setSoldUnits(soldUnits)
        
        #raise Exception("Code with multiple products.")

def getProduct(row):
    prod = None
    if row['CATEGORÍA']=='MEDICAMENTOS':
        prod = QantuMedicine(row['CÓDIGO'], row['NOMBRE'].upper(), row['CANTIDAD'],
                             row['disable (EXTRA)'], row['creado (EXTRA)'], row['STOCK MÍNIMO'],
                             row['PRECIO DE VENTA'], row['PRECIO DE COMPRA'])
    elif row['CATEGORÍA']=='GALENICOS':
        prod = QantuGalenico(row['CÓDIGO'], row['NOMBRE'].upper(), row['CANTIDAD'],
                             row['disable (EXTRA)'], row['creado (EXTRA)'], row['STOCK MÍNIMO'],
                             row['PRECIO DE VENTA'], row['PRECIO DE COMPRA'])
    elif row['CATEGORÍA']=='DISPOSITIVOS MEDICOS':
        prod = QantuDevice(row['CÓDIGO'], row['NOMBRE'].upper(), row['CANTIDAD'],
                           row['disable (EXTRA)'], row['creado (EXTRA)'], row['STOCK MÍNIMO'],
                             row['PRECIO DE VENTA'], row['PRECIO DE COMPRA'])
    else:
        prod = QantuGeneral(row['CÓDIGO'], row['NOMBRE'].upper(), row['CANTIDAD'],
                            row['disable (EXTRA)'], row['CATEGORÍA'], row['creado (EXTRA)'], row['STOCK MÍNIMO'],
                             row['PRECIO DE VENTA'], row['PRECIO DE COMPRA'])
    
    prod.setBrand(row['Lab (EXTRA)'])
    prod.setOtc(row['otc (EXTRA)'])
    return prod

def getPackage(pack_df, code):
    sub_df = pack_df.loc[pack_df['CÓDIGO'] == code]
    if len(sub_df)>0:
        row = sub_df.iloc[0]
        pack = QantuPackage(row['CÓDIGO'], row['NOMBRE'])
        for index, row in sub_df.iterrows():
            #print(f"Adding {row['NOMBRE (ITEM)']} X {row['CANTIDAD (ITEM)']} to {row['NOMBRE']}")
            pack.addItem(row['CÓDIGO (ITEM)'], row['CANTIDAD (ITEM)'])
        return pack
    else:
        #print(f"Package {code} not found, invalid or deleted")
        return None

# Combine galenics items with same form and concentration
def combineGalenicos(prodDict):
    print("Third product filter")
    for code in list(prodDict):
        if not code in prodDict:
            continue
        prod = prodDict[code]
        if prod.getCategory() is not 'GALENICOS':
            continue
        #print("Get formula")
        formu = prod.getFormula()
        if formu == "":
            print("WARNING: Invalid formula["+prod.getName()+"]")
            continue
        ##print("Get CC")
        cc = prod.getConcentration()

        ##print("Get Qtty")
        qtty = prod.getQtty()
        if qtty == "":
            print("WARNING: Invalid qtty["+prod.getName()+"]")
            continue

        for code2 in list(prodDict):
            if code == code2:
                continue
            if not code in prodDict:
                continue
            prod2 = prodDict[code2]
            if prod2.getCategory() is not 'GALENICOS':
                continue
            
            if formu == prod2.getFormula():
                if cc == prod2.getConcentration():
                    if qtty == prod2.getQtty():
                        prod.merge(prod2)
                        del prodDict[code2]
    return prodDict

# Combine med devs items with same type, mark, subcategory, qtty and units
def combineMedDevices(prodDict):
    print("Fourth product filter")
    for code in list(prodDict):
        if not code in prodDict:
            continue
        prod = prodDict[code]
        if prod.getCategory()!='DISPOSITIVOS MEDICOS':
            continue
        typ = prod.getType()
        if typ == "":
            print("WARNING: Invalid device type["+prod.getName()+"]")
            continue
        ch = prod.getCharacteristic()
        if ch == "":
            print("WARNING: Invalid device characteristic["+prod.getName()+"]")
            continue
        qtty = prod.getQtty()
        if qtty == "":
            print("WARNING: Invalid device qtty["+prod.getName()+"]")
            continue

        for code2 in list(prodDict):
            if code == code2:
                continue
            if not code in prodDict:
                continue
            prod2 = prodDict[code2]
            if prod2.getCategory()!='DISPOSITIVOS MEDICOS':
                continue
            if typ == prod2.getType():
                if ch == prod2.getCharacteristic():
                    if qtty == prod2.getQtty():
                        prod.merge(prod2)
                        del prodDict[code2]
    return prodDict

# Combine med devs items with same type, mark, subcategory, qtty and units
def combineAseo(prodDict):
    print("Five product filter")
    for code in list(prodDict):
        if not code in prodDict:
            continue
        prod = prodDict[code]
        if prod.getCategory() not in ['ASEO', 'BELLEZA', 'BEBES']:
            continue
        #print("ASEO1:"+prod.getName())
        typ = prod.getType()
        #print(typ)
        if typ == "":
            print("WARNING: Invalid general type["+prod.getName()+"]")
            continue
        brand = prod.getBrand()
        #print(brand)
        if brand == "":
            print("WARNING: Invalid general brand["+prod.getName()+"]")
            continue
        ch = prod.getCharacteristic()
        #print(ch)
        if ch == "":
            print("WARNING: Invalid general characteristic["+prod.getName()+"]")
            continue
        cnt = prod.getContent()
        #print(cnt)
        if cnt == "":
            print("WARNING: Invalid general content["+prod.getName()+"]")
            continue

        for code2 in list(prodDict):
            if code == code2:
                continue
            if not code in prodDict:
                continue
            prod2 = prodDict[code2]
            if prod2.getCategory() not in ['ASEO', 'BELLEZA', 'BEBES']:
                continue

            if typ == prod2.getType():
                if brand == prod2.getBrand():
                    if cnt == prod2.getContent():
                        #print("Match!")
                        prod.merge(prod2)
                        del prodDict[code2]
    return prodDict

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

    for key, prod in prodDict.items():
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


now = (datetime.now()+ timedelta(days=1)).strftime("%Y-%m-%d")

# download sales per product
repHeaders = ["CÓDIGO", "NOMBRE", "STOCK ACTUAL",
              "ÚLTIMO PROVEEDOR", "CANTIDAD TOTAL"]
rd = ReportDownloader("Exportar ventas por producto.xlsx", "export_sales_per_product",
                      repHeaders, '2023-05-27',
                      now)
file_sales = rd.execute()
if file_sales == "":
    sys.exit("Can't dowloand file[Exportar ventas por producto.xlsx]")

# download product data
repHeaders = ["CÓDIGO", "NOMBRE", "STOCK MÍNIMO", "CANTIDAD", "disable (EXTRA)",
              "creado (EXTRA)", "Lab (EXTRA)", "otc (EXTRA)", "CATEGORÍA", "PRECIO DE VENTA", "PRECIO DE COMPRA"]
rd = ReportDownloader("Exportar productos.xlsx", "export_products",
                      repHeaders, '2024-02-12',
                      now)
file_prod = rd.execute()
if file_prod == "":
    sys.exit("Can't dowloand file[Exportar productos.xlsx]")

#download package data
repHeaders = ["CÓDIGO", "NOMBRE", "CÓDIGO (ITEM)", "NOMBRE (ITEM)", 
              "CANTIDAD (ITEM)"]
rd = ReportDownloader("Exportar paquetes.xlsx", "export_packages",
                      repHeaders, '2024-02-12',
                      now)
file_pack = rd.execute()
if file_pack == "":
    sys.exit("Can't dowloand file[Exportar productos.xlsx]")

prodSale_df = pandas.read_excel(file_sales, skiprows=5)
print("REG SIZE (prod sales):"+str(len(prodSale_df)))

prod_df = pandas.read_excel(file_prod, skiprows=4)
print("REG SIZE (prod):"+str(len(prod_df)))

pack_df = pandas.read_excel(file_pack, skiprows=4)
print("REG SIZE (prod):"+str(len(prod_df)))

# Load products
for index, row in prod_df.iterrows():
    prod = getProduct(row)
    if prod != None and not prod.isDisable() and not prod.isNoUsar():
        addSaleData(prod, prodSale_df)
        if prod.getCode() in prodDict:
            raise Exception("Key must be unique")
        prodDict[prod.getCode()]=prod

# Load packages
for key, row in prodSale_df.iterrows():
    # only add sales that are products
    pack = getPackage(pack_df, row['CÓDIGO'])
    if pack is not None:
        pack.setSoldUnits(row['CANTIDAD TOTAL'])
        packDict[pack.getCode()]=pack
        
# Incresase sold unit according to package
print("First product filter")
for pack in packDict.values():
    for packprodCode, qty in pack.getItems().items():
        if packprodCode in prodDict.keys():
            prodDict[packprodCode].addSoldUnits(qty*pack.getSoldUnits())

# Combine medicine items with same form and concentration
print("Second product filter")
for code in list(prodDict):
    if not code in prodDict:
        continue
    prod = prodDict[code]
    if prod.getCategory() is not 'MEDICAMENTOS':
        continue
    formu = prod.getFormula()
    if formu == "":
        print("WARNING: Invalid formula for MED "+prod.getName())
        continue
    cc = prod.getConcentration()
    if cc == "":
        print("WARNING: Invalid CC for MED ")
        continue
    ff  = prod.getFF()
    if ff == "":
        print("WARNING: Invalid FF for MED ")
        continue

    for code2 in list(prodDict):
        if code == code2:
            continue
        if not code in prodDict:
            continue
        prod2 = prodDict[code2]
        if prod2.getCategory() is not 'MEDICAMENTOS':
            continue
        
        if formu == prod2.getFormula():
            if cc == prod2.getConcentration():
                if ff == prod2.getFF():
                    prod.merge(prod2)
                    del prodDict[code2]

prodDict=combineGalenicos(prodDict)
prodDict=combineMedDevices(prodDict)
#prodDict=combineAseo(prodDict)

medsDict = {}
otherDict = {}
for key, prod in prodDict.items():
    if prod.getCategory()=='MEDICAMENTOS':
        medsDict[key]=prod
    else:
        otherDict[key]=prod

dataMeds = createDataList(medsDict)
dataOther = createDataList(otherDict)
countMeds = len(dataMeds)
countOther =len(dataOther)

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
    #for prov in providers:
        #dataProvList = createDataProvList(prov, countMeds)
        #prov_df = pandas.DataFrame(dataProvList, columns = cols)
        #prov_df.to_excel(excel_writer, sheet_name='Lista_'+prov, index=False)