import sys, os
sys.path.append('../')
from lib.libclass import *
from lib.ReportDownloader import *
import pandas
from datetime import datetime
import re
import calendar

prodDBDict = {}
prodDict = {}
packDict = {}

colCosto = 'D'
colPrecio = 'E'
colVentas = 'F'
colMargen = 'H'

IGV=0.18

# Read JSON file
with open('../lib/cfg.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
    business_ = data["businessId"]


def addSaleData(prod, sale_df):
    sub_df = sale_df.loc[sale_df['CÓDIGO'] == prod.getCode()]
    if len(sub_df)==1:
        row = sub_df.iloc[0]
        # add sale data
        #prod.setLastProvider(row['ÚLTIMO PROVEEDOR'])
        prod.setSoldUnits(row['CANTIDAD TOTAL'])
    elif len(sub_df)==0:
        #print("Product ["+prod.getName()+"] never sale!")
        prod.setSoldUnits(0)
    else:
        raise Exception("Code with multiple products.")

def getProductDB(row):
    return QantuProduct(row['CÓDIGO'], row['NOMBRE'], row['CANTIDAD'],
                            row['disable (EXTRA)'], row['CATEGORÍA'], row['creado (EXTRA)'], row['STOCK MÍNIMO'],
                             row['PRECIO DE VENTA'], row['PRECIO DE COMPRA'])

def getProduct(prod_df, code):
    sub_df = prod_df.loc[prod_df['CÓDIGO'] == code]
    if len(sub_df)>0:
        row = sub_df.iloc[0]
        return QantuProduct(row['CÓDIGO'], row['NOMBRE'], row['CANTIDAD'],
                                row['disable (EXTRA)'], row['CATEGORÍA'], row['creado (EXTRA)'], row['STOCK MÍNIMO'],
                                 row['PRECIO DE VENTA'], row['PRECIO DE COMPRA'])
    else:
        return None

def getPackage(pack_df, code):
    sub_df = pack_df.loc[pack_df['CÓDIGO'] == code]
    if len(sub_df)>0:
        row = sub_df.iloc[0]
        pack = QantuPackage(row['CÓDIGO'], row['NOMBRE'], row['PRECIO DE VENTA'], category=row['CATEGORÍA'])
        cost = 0
        pName = pack.getName()
        for index, row in sub_df.iterrows():
            #print(f"Adding {row['NOMBRE (ITEM)']} X {row['CANTIDAD (ITEM)']} to {row['NOMBRE']}")
            cantItem = row['CANTIDAD (ITEM)']
            codeItem = row['CÓDIGO (ITEM)']
            pack.addItem(codeItem, cantItem)
            if codeItem in prodDBDict:
                prod = prodDBDict[codeItem]
                cost=cost+cantItem*prod.getLastCost()
            else:
                print(f"Package {code}[{pName}] item not found {codeItem}")
            
        pack.setCost(cost)
        return pack
    else:
        return None

def createDataList(packDict, prodDict):
    data = []
    summary = {}
    count = 0

    for key, prod in prodDict.items():
        count = count + 1
        mcu = '={colP}{rowP}-{colC}{rowC}'.format(colP=colPrecio, rowP=count+1,
                                                  colC=colCosto, rowC=count+1)
        mcup = '= {colM}{rowM}/{colP}{rowP}'.format(colM=colMargen, rowM=count+1,
                                                    colP=colPrecio, rowP=count+1)
        mc = '= {colM}{rowM}*{colV}{rowV}'.format(colM=colMargen, rowM=count+1,
                                                    colV=colVentas, rowV=count+1)
        total = prod.getPrice()*prod.getSoldUnits()
        l = [prod.getCode(), prod.getName(), prod.getCategory(),
                     prod.getLastCost(), prod.getPrice(), prod.getSoldUnits(),
                     total, mcu, mcup, mc]
        data.append(l)
        cat = prod.getCategory()
        mcVal = (prod.getPrice()-prod.getLastCost())*prod.getSoldUnits()
        mcrVal = mcVal/(1+IGV)
        if cat in summary:
            summary[cat][0]=summary[cat][0]+total
            summary[cat][1]=summary[cat][1]+mcVal
            summary[cat][2]=summary[cat][2]+mcrVal
        else:
            summary[cat]=[total, mcVal, mcrVal]
        
    for key, pack in packDict.items():
        count = count + 1
        mcu = '={colP}{rowP}-{colC}{rowC}'.format(colP=colPrecio, rowP=count+1,
                                                  colC=colCosto, rowC=count+1)
        mcup = '= {colM}{rowM}/{colP}{rowP}'.format(colM=colMargen, rowM=count+1,
                                                    colP=colPrecio, rowP=count+1)
        mc = '= {colM}{rowM}*{colV}{rowV}'.format(colM=colMargen, rowM=count+1,
                                                    colV=colVentas, rowV=count+1)
        total = pack.getPrice()*pack.getSoldUnits()
        l = [pack.getCode(), pack.getName(), pack.getCategory(), 
                     pack.getCost(), pack.getPrice(), pack.getSoldUnits(),
                     total, mcu, mcup, mc]
        data.append(l)
        cat = pack.getCategory()
        mcVal = (pack.getPrice()-pack.getCost())*pack.getSoldUnits()
        mcrVal = mcVal/(1+IGV)
        if cat in summary:
            summary[cat][0]=summary[cat][0]+total
            summary[cat][1]=summary[cat][1]+mcVal
            summary[cat][2]=summary[cat][2]+mcrVal
        else:
            summary[cat]=[total, mcVal, mcrVal]
        
    
    summaryData=[]
    for key in summary:
        summaryData.append([key, summary[key][0], summary[key][1], summary[key][2]])
    
    return data, summaryData

# Enter period
year = input("Enter year YYYY: ")
month = input("Enter month mm: ")
beginDt = year+"-"+month+"-01"
#lastDay = calendar.monthrange(int(year), int(month))[1]
monthNum=int(month)
endMonthNum = monthNum+1
if endMonthNum == 13:
    endMonthNum=1
    yearNum = int(year)+1
    year = str(yearNum)
endMonth = "{:02d}".format(endMonthNum)
endDt = year+"-"+endMonth+"-01"

now = datetime.now().strftime("%Y-%m-%d")

# download sales per product
repHeaders = ["CÓDIGO", "NOMBRE", "CANTIDAD TOTAL"]
rd = ReportDownloader("Exportar ventas por producto.xlsx", "export_sales_per_product",
                      repHeaders, beginDt,
                      endDt)
file_sales = rd.execute()
if file_sales == "":
    sys.exit("Can't dowloand file[Exportar ventas por producto.xlsx]")

# download product data
repHeaders = ["CÓDIGO", "NOMBRE", "STOCK MÍNIMO", "CANTIDAD", "disable (EXTRA)",
              "creado (EXTRA)", "CATEGORÍA", "PRECIO DE VENTA", "PRECIO DE COMPRA"]
rd = ReportDownloader("Exportar productos.xlsx", "export_products",
                      repHeaders, '2024-02-12',
                      now)
file_prod = rd.execute()
if file_prod == "":
    sys.exit("Can't dowloand file[Exportar productos.xlsx]")

#download package data
repHeaders = ["CÓDIGO", "NOMBRE", "CÓDIGO (ITEM)", "NOMBRE (ITEM)", 
              "CANTIDAD (ITEM)", "CATEGORÍA", "PRECIO DE VENTA"]
rd = ReportDownloader("Exportar paquetes.xlsx", "export_packages",
                      repHeaders, '2024-02-12',
                      now)
file_pack = rd.execute()
if file_pack == "":
    sys.exit("Can't dowloand file[Exportar productos.xlsx]")

#download expenses
repHeaders = ["DESCRIPCIÓN", "CATEGORÍA", "MONTO"]
rd = ReportDownloader("Exportar gastos.xlsx", "export_payments_expenses",
                      repHeaders, beginDt, endDt)
file_expenses = rd.execute()
if file_expenses == '':
    sys.exit("Can't dowloand file[Exportar gastos.xlsx]")
    

prodSale_df = pandas.read_excel(file_sales, skiprows=5)
print("REG SIZE (prod sales):"+str(len(prodSale_df)))

prod_df = pandas.read_excel(file_prod, skiprows=4)
print("REG SIZE (prod):"+str(len(prod_df)))

pack_df = pandas.read_excel(file_pack, skiprows=4)
print("REG SIZE (pack):"+str(len(pack_df)))

exp_df = pandas.read_excel(file_expenses, skiprows=4)
print("REG SIZE (expenses):"+str(len(exp_df)))

sum_row = exp_df[['MONTO']].sum()
sum_row['DESCRIPCIÓN'] = 'Total'
sum_row['CATEGORÍA'] = 'Todas'
sum_df = pandas.DataFrame([sum_row], columns=exp_df.columns)
exp_df = pandas.concat([exp_df, sum_df], ignore_index=True)

# Load products DB
for index, row in prod_df.iterrows():
    prod = getProductDB(row)
    if prod != None and (not prod.isDisable()) and not prod.isNoUsar():
        addSaleData(prod, prodSale_df)
        if prod.getCode() in prodDBDict:
            raise Exception("Key must be unique")
        prodDBDict[prod.getCode()]=prod

# Load products
for index, row in prodSale_df.iterrows():
    prod = getProduct(prod_df, row['CÓDIGO'])
    if prod != None and (not prod.isDisable()) and not prod.isNoUsar():
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

data, summaryData = createDataList(packDict, prodDict)
count = len(data)

cols = ['COD', 'NOMBRE', 'CATEGORIA', 'COSTO', 'PRECIO', 'VENTAS',
        'TOTAL', 'Mcu', 'Mcu%', 'Mc']
out_df = pandas.DataFrame(data, columns = cols)

colsSummary = ['CAT', 'VOL VENTAS', 'MC', 'MCR']
out2_df = pandas.DataFrame(summaryData, columns = colsSummary)
sum_row = out2_df[['VOL VENTAS', 'MC', 'MCR']].sum()
sum_row['CAT'] = 'Total'
sum_df = pandas.DataFrame([sum_row], columns=out2_df.columns)
out2_df = pandas.concat([out2_df, sum_df], ignore_index=True)

now = datetime.now().strftime("%Y%m%d")
excel_name = str(business_)+'_Utilidad_'+year+month+'_'+now+'.xlsx'

with pandas.ExcelWriter(excel_name) as excel_writer:
    out_df.to_excel(excel_writer, sheet_name='Utilidad', index=False)
    out2_df.to_excel(excel_writer, sheet_name='Summary', index=False)
    exp_df.to_excel(excel_writer, sheet_name='Expenses', index=False)