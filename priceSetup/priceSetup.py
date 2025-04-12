import sys, os
sys.path.append(r'../')
from lib.libclass import *
from lib.ReportDownloader import *
import pandas
from datetime import datetime
import re


colCosto = 'D'
colPrecio = 'E'
colMargen = 'F'
colMargenx = 'H'
    
prodDict = {}
packDict = {}
igv = 0.18
igvC = 1-igv

def getProduct(prod_df, code):
    sub_df = prod_df.loc[prod_df['CÓDIGO'] == code]
    if len(sub_df)==1:
        row = sub_df.iloc[0]
        prod = None
        if row['CATEGORÍA']=='MEDICAMENTOS':
            prod = QantuMedicine(row['CÓDIGO'], row['NOMBRE'], row['CANTIDAD'],
                                 row['disable (EXTRA)'], row['creado (EXTRA)'], row['STOCK MÍNIMO'])
            #print("generic value "+row['NOMBRE'])
            #print(row['generico (EXTRA)'])
            #print(type(row['generico (EXTRA)']))
            prod.setGenerico(row['generico (EXTRA)'])
            #print(prod.getName())
            #print(prod.isGenerico())
        elif row['CATEGORÍA']=='GALENICOS':
            prod = QantuGalenico(row['CÓDIGO'], row['NOMBRE'], row['CANTIDAD'],
                                 row['disable (EXTRA)'], row['creado (EXTRA)'], row['STOCK MÍNIMO'])
        elif row['CATEGORÍA']=='DISPOSITIVOS MEDICOS':
            prod = QantuDevice(row['CÓDIGO'], row['NOMBRE'], row['CANTIDAD'],
                               row['disable (EXTRA)'], row['creado (EXTRA)'], row['STOCK MÍNIMO'])
        else:
            prod = QantuGeneral(row['CÓDIGO'], row['NOMBRE'], row['CANTIDAD'],
                                row['disable (EXTRA)'], row['CATEGORÍA'], row['creado (EXTRA)'],
                                row['STOCK MÍNIMO'])
        # add data
        prod.setLastCost(row['PRECIO DE COMPRA'])
        prod.setPrice(row['PRECIO DE VENTA'])
        return prod
    elif len(sub_df)==0:
        print("Product not found")
        return None
    else:
        raise Exception("Code with multiple products.")
    

def getPackage(pack_df, code):
    sub_df = pack_df.loc[pack_df['CÓDIGO'] == code]
    if len(sub_df)>0:
        row = sub_df.iloc[0]
        pack = QantuPackage(row['CÓDIGO'], row['NOMBRE'], row['PRECIO DE VENTA'],
                            category=row['CATEGORÍA'])
        cost = 0
        pName = pack.getName()
        for index, row in sub_df.iterrows():
            #print(f"Adding {row['NOMBRE (ITEM)']} X {row['CANTIDAD (ITEM)']} to {row['NOMBRE']}")
            cantItem = row['CANTIDAD (ITEM)']
            codeItem = row['CÓDIGO (ITEM)']
            pack.addItem(codeItem, cantItem)
            if codeItem in prodDict:
                prod = prodDict[codeItem]
                cost=cost+cantItem*prod.getLastCost()
                if prod.getCategory()=='MEDICAMENTOS':
                    pack.setGenerico(prod.isGenerico())
            else:
                print(f"Package {code}[{pName}] item not found {codeItem}")
            
        pack.setCost(cost)
        return pack
    else:
        #print(f"Package {code} not found, invalid or deleted")
        return None

def createDataList(prodDict):
    data = []
    count = 0

    for key, prod in prodDict.items():
        count = count + 1
        mcu = '={colP}{rowP}-{colC}{rowC}'.format(colP=colPrecio, rowP=count+1,
                                                  colC=colCosto, rowC=count+1)
        mcup = '= {colM}{rowM}/{colP}{rowP}'.format(colM=colMargen, rowM=count+1,
                                                    colP=colPrecio, rowP=count+1)
        
        #if prod.getCategory()=='MEDICAMENTOS':
        #    print("Here: "+prod.getName())
         #   print(prod.isGenerico())
        mcups = 0
        #if prod.getCategory()=='MEDICAMENTOS':
        #    print(prod.getCategory())
        #    print(prod.isGenerico())
        
        if prod.getCategory()=='MEDICAMENTOS' and prod.isGenerico():
            #print(prod.getFF())
            if prod.getFF() in ['TAB', 'CAP', 'TAB_REC']:
                mcups_r = 0.55
                mcups = '='+str(mcups_r)
                #print(mcups)
            else:
                mcups_r = 0.3
                mcups = '='+str(mcups_r)
        else:
            mcups_r = 0.1
            mcups = '='+str(mcups_r)
        presug = '={colC}{rowC}/(1-{colMx}{rowMx})'.format(colC=colCosto, rowC=count+1,
                                                    colMx=colMargenx, rowMx=count+1)
        data.append( [prod.getCode(), prod.getName(), prod.getCategory(), prod.getLastCost(),
                      prod.getPrice(), mcu, mcup, mcups, presug])
    return data

def createDataListPack(packDict):
    data = []
    count = 0

    for key, pack in packDict.items():
        count = count + 1
        mcu = '={colP}{rowP}-{colC}{rowC}'.format(colP=colPrecio, rowP=count+1,
                                                  colC=colCosto, rowC=count+1)
        mcup = '= {colM}{rowM}/{colP}{rowP}'.format(colM=colMargen, rowM=count+1,
                                                    colP=colPrecio, rowP=count+1)
        mcups = 0
        if pack.getCategory()=='MEDICAMENTOS' and pack.isGenerico():
            mcups_r = 0.35
            mcups = '='+str(mcups_r)
        else:
            mcups_r = 0.1
            mcups = '='+str(mcups_r)
        presug = '={colC}{rowC}/(1-{colMx}{rowMx})'.format(colC=colCosto, rowC=count+1,
                                                    colMx=colMargenx, rowMx=count+1)
        data.append( [pack.getCode(), pack.getName(), pack.getCategory(), pack.getCost(),
                      pack.getPrice(), mcu, mcup, mcups, presug])
    return data

today = datetime.now().strftime("%Y-%m-%d")

# download product data
repHeaders = ["CÓDIGO", "NOMBRE", "STOCK MÍNIMO", "CANTIDAD", "disable (EXTRA)",
              "creado (EXTRA)", "CATEGORÍA", "PRECIO DE VENTA", "PRECIO DE COMPRA",
              "generico (EXTRA)"]
rd = ReportDownloader("Exportar productos.xlsx", "export_products",
                      repHeaders, '2024-02-12',
                      today)
file_prod = rd.execute()
if file_prod == "":
    sys.exit("Can't dowloand file[Exportar productos.xlsx]")

#download package data
repHeaders = ["CÓDIGO", "NOMBRE", "CÓDIGO (ITEM)", "NOMBRE (ITEM)", 
              "CANTIDAD (ITEM)", "CATEGORÍA", "PRECIO DE VENTA"]
rd = ReportDownloader("Exportar paquetes.xlsx", "export_packages",
                      repHeaders, '2024-02-12',
                      today)
file_pack = rd.execute()
if file_pack == "":
    sys.exit("Can't dowloand file[Exportar productos.xlsx]")

prod_df = pandas.read_excel(file_prod, skiprows=4)
print("REG SIZE (prod):"+str(len(prod_df)))

pack_df = pandas.read_excel(file_pack, skiprows=4)
print("REG SIZE (prod):"+str(len(prod_df)))

# Load products
for index, row in prod_df.iterrows():
    # only add sales that are products
    prod = getProduct(prod_df, row['CÓDIGO'])
    if prod is not None and not prod.isDisable() and not prod.isNoUsar():
        # add product to data dict
        if prod.getCode() in prodDict:
            raise Exception("Key must be unique")
        prodDict[prod.getCode()]=prod
        #if prod.getCategory()=='MEDICAMENTOS':
        #    print(prod.getName())
        #    print(prod.isGenerico())

# Load packages
for key, row in pack_df.iterrows():
    # only add sales that are products
    pack = getPackage(pack_df, row['CÓDIGO'])
    if pack is not None:
        packDict[pack.getCode()]=pack


medsDict = {}
otherDict = {}
for key, prod in prodDict.items():
    if prod.getCategory()=='MEDICAMENTOS':
        medsDict[key]=prod
    else:
        otherDict[key]=prod

dataMeds = createDataList(medsDict)
dataOther = createDataList(otherDict)
dataPack = createDataListPack(packDict)

cols = ['COD', 'NOMBRE', 'CATEGORIA', 'COSTO', 'PRECIO', 'MCu', 
        'MCup', 'MCups', 'SUGERIDO' ]

outMed_df = pandas.DataFrame(dataMeds, columns = cols)
outOther_df = pandas.DataFrame(dataOther, columns = cols)
outPack_df = pandas.DataFrame(dataPack, columns = cols)

now = datetime.now().strftime("%Y%m%d")
excel_name = 'PriceSetup_'+now+'.xlsx'

with pandas.ExcelWriter(excel_name) as excel_writer:
    outMed_df.to_excel(excel_writer, sheet_name='Medicamentos', index=False)
    outOther_df.to_excel(excel_writer, sheet_name='Otros', index=False)
    outPack_df.to_excel(excel_writer, sheet_name='Paquetes', index=False)