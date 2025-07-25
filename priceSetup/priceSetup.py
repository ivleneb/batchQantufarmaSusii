import sys #, os
sys.path.append(r'../')
from lib.libclass import *
from lib.ReportDownloader import *
import pandas
from datetime import datetime
#import re


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
        #"CÓDIGO",
        #"NOMBRE"
        prod.setAlias(row["ALIAS"])
        prod.setUnidad(row["UNIDAD"])
        prod.setPrice(row['PRECIO DE VENTA'])
        prod.setLastCost(row['PRECIO DE COMPRA'])
        #"CANTIDAD",
        prod.setNumRegSan(row["num_regsan (EXTRA)"])
        prod.setBrand(row["lab (EXTRA)"])
        #"disable (EXTRA)",
        #"creado (EXTRA)",
        prod.setGenerico(row['generico (EXTRA)'])
        prod.setFechaVto(row["fecha_vto (EXTRA)"])
        prod.setNroLote(row["nro_lote (EXTRA)"])
        prod.setAdicional(row["adicional (EXTRA)"])
        prod.setOtc(row["otc (EXTRA)"])
        prod.setTempAlm(row["temp_alm (EXTRA)"])
        prod.setUnitsBlister(row["units_blister (EXTRA)"])
        prod.setUnitsCaja(row["units_caja (EXTRA)"])
        prod.setMonedaDeVenta(row["MONEDA DE VENTA"])
        prod.setMonedaDeCompra(row["MONEDA DE COMPRA"])
        prod.setConStock(row["CON STOCK"])
        #"CATEGORÍA"
        prod.setImpuesto(row["IMPUESTO"])
        prod.setPesoBruto(row["PESO BRUTO (KGM)"])
        #"STOCK MÍNIMO"
        prod.setPorcentajeDeGanancia(row["PORCENTAJE DE GANANCIA"])
        prod.setDescuento(row["DESCUENTO"])
        prod.setTipoDeDescuento(row["TIPO DE DESCUENTO"])
        prod.setBusquedaDesdeVentas(row["BÚSQUEDA DESDE VENTAS"])
        prod.setCategoriaSunat(row["CATEGORÍA SUNAT"])
        
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
                            category=row['CATEGORÍA'], alias=row['ALIAS'], unidad=row['UNIDAD'])
        cost = 0
        pName = pack.getName()
        for index, row in sub_df.iterrows():
            #print(f"Adding {row['NOMBRE (ITEM)']} X {row['CANTIDAD (ITEM)']} to {row['NOMBRE']}")
            cantItem = row['CANTIDAD (ITEM)']
            codeItem = row['CÓDIGO (ITEM)']
            pack.addItem(codeItem, cantItem)
            if codeItem in prodDict:
                prod = prodDict[codeItem]
                pack.addItemObj(prod)
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
        
        mcups = 0
        
        forma_far = ''
        is_gen = ''
        if prod.getCategory()=='MEDICAMENTOS' and prod.isGenerico():
            #print(prod.getFF())
            if prod.getFF() in ['TAB', 'CAP', 'TAB_REC']:
                mcups_r = 0.55
                mcups = '='+str(mcups_r)
                #print(mcups)
            else:
                mcups_r = 0.3
                mcups = '='+str(mcups_r)
            forma_far = prod.getFF()
            is_gen = prod.isGenerico()
            
        else:
            mcups_r = 0.15
            mcups = '='+str(mcups_r)
            if prod.getCategory()=='MEDICAMENTOS':
                forma_far = prod.getFF()
                is_gen = prod.isGenerico()
                
        presug = '={colC}{rowC}/(1-{colMx}{rowMx})'.format(colC=colCosto, rowC=count+1,
                                                    colMx=colMargenx, rowMx=count+1)
        data.append( [prod.getCode(), prod.getName(), prod.getCategory(), prod.getLastCost(),
                      prod.getPrice(), mcu, mcup, mcups, presug, forma_far, is_gen])
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
            forma_far = prod.getFF()
            is_gen = pack.isGenerico()
        else:
            mcups_r = 0.15
            mcups = '='+str(mcups_r)
        presug = '={colC}{rowC}/(1-{colMx}{rowMx})'.format(colC=colCosto, rowC=count+1,
                                                    colMx=colMargenx, rowMx=count+1)
        data.append( [pack.getCode(), pack.getName(), pack.getCategory(), pack.getCost(),
                      pack.getPrice(), mcu, mcup, mcups, presug, '', ''])
    return data

def createDataListToImport(prodDict):
    data = []
    count = 0

    for key, prod in prodDict.items():
        count = count + 1
        
        mcups = 0

        if prod.getCategory()=='MEDICAMENTOS' and prod.isGenerico():
            if prod.getFF() in ['TAB']:
                if prod.getLastCost()<=0.5:
                    mcups = 0.7
                elif prod.getLastCost()>0.5 and prod.getLastCost()<=0.8:
                    mcups = 0.67
                else:
                    mcups = 0.63
            else:
                continue
        else:
            continue
        
        gan_per = (mcups/(1-mcups))
        gan_per = round(gan_per, 4)
        prod.setPorcentajeDeGanancia(gan_per*100)
        presug = round((1+gan_per)*prod.getLastCost(), 1)
        print("precio sugerido:"+str(presug))
        prod.setPrice(presug)
        if presug < 0.5:
            prod.setPrice(0.5)
            prod.setPorcentajeDeGanancia('')
        
        ls = [ prod.getCode(), prod.getName(), prod.getAlias(), prod.getUnidad(),
            prod.getPrice(), prod.getLastCost(), prod.getStock(), prod.getNumRegSan(),
            prod.getBrand(), prod.getDisable(), prod.getCreatedAt(), prod.getGenerico(),
            prod.getFechaVto(), prod.getNroLote(), prod.getAdicional(), prod.getOtc(),
            prod.getTempAlm(), prod.getUnitsBlister(), prod.getUnitsCaja(), prod.getMonedaDeVenta(),
            prod.getMonedaDeCompra(), prod.getConStock(), prod.getCategory(),  prod.getImpuesto(),
            prod.getPesoBruto(), prod.getMinStock(), prod.getPorcentajeDeGanancia(), prod.getDescuento(),
            prod.getTipoDeDescuento(), prod.getBusquedaDesdeVentas(), prod.getCategoriaSunat()
        ]
        
        data.append(ls)
    return data

def createDataListToImportPack(prodDict, packDict):
    data = []
    count = 0

    for key, prod in prodDict.items():
        count = count + 1

        if prod.getCategory()=='MEDICAMENTOS' and prod.isGenerico():
            if prod.getFF() in ['TAB']:
                hasPack=False
                for key, pack in packDict.items():
                    if prod.getCode() in pack.itemsObj :
                        if len(pack.itemsObj)==1:
                            hasPack=True
                            print("PROD["+prod.getName()+"] already has pack["+pack.getName()+"].")
                            cantidadItem = pack.items[prod.getCode()]
                            ls = [ pack.getCode(), pack.getName(), pack.getAlias(), pack.getUnidad(),
                                pack.getPrice(),  pack.getCategory(), prod.getCode(), prod.getName(),
                                prod.getAlias(), prod.getUnidad(), prod.getPrice(), cantidadItem
                            ]
                            
                            data.append(ls)
                            
                            if prod.getUnitsBlister()!= cantidadItem:
                                print("WARNING. UnitsBlister different from CANTIDAD (ITEM)")
                        else:
                            print("PACK["+pack.getName()+"] has more than 1 item.")
                if not hasPack:
                    print("NO_PACK PROD["+prod.getName()+"] hasn't pack. Create!")
                    cantidadItem = int(prod.getUnitsBlister())
                    
                    if cantidadItem == int(prod.getUnitsBlister())==1:
                        print("WARNING prod["+prod.getName()+"] has unitsBlister["+str(cantidadItem)+"]")
                        continue
                    
                    packPrice = round(prod.getPrice()*cantidadItem*0.8,1)
                    packName = "Blister "+prod.getName()+"X"+str(cantidadItem)
                    ls = [ prod.getCode()+"BLI"+str(cantidadItem), packName, "", "UNIDAD",
                        packPrice,  prod.getCategory(), prod.getCode(), prod.getName(),
                        "", prod.getUnidad(), prod.getPrice(), cantidadItem
                    ]
                    data.append(ls)
                    print(ls)
                    
            else:
                continue
        else:
            continue
    return data



today = datetime.now().strftime("%Y-%m-%d")

# download product data
repHeaders = ["CÓDIGO", "NOMBRE", "ALIAS", "UNIDAD", "PRECIO DE VENTA", "PRECIO DE COMPRA", "CANTIDAD",
        "num_regsan (EXTRA)", "lab (EXTRA)", "disable (EXTRA)", "creado (EXTRA)", "generico (EXTRA)", "fecha_vto (EXTRA)",
        "nro_lote (EXTRA)", "adicional (EXTRA)", "otc (EXTRA)", "temp_alm (EXTRA)", "units_blister (EXTRA)",
        "units_caja (EXTRA)", "MONEDA DE VENTA", "MONEDA DE COMPRA", "CON STOCK", "CATEGORÍA",
        "IMPUESTO", "PESO BRUTO (KGM)", "STOCK MÍNIMO", "PORCENTAJE DE GANANCIA", "DESCUENTO", "TIPO DE DESCUENTO",
        "BÚSQUEDA DESDE VENTAS", "CATEGORÍA SUNAT"]
rd = ReportDownloader("Exportar productos.xlsx", "export_products",
                      repHeaders, '2024-02-12',
                      today)
file_prod = rd.execute()
if file_prod == "":
    sys.exit("Can't dowloand file[Exportar productos.xlsx]")

#download package data
repHeaders = ["CÓDIGO", "NOMBRE", "ALIAS", "UNIDAD", "PRECIO DE VENTA", "CATEGORÍA", "CÓDIGO (ITEM)", "NOMBRE (ITEM)",
          "ALIAS (ITEM)", "UNIDAD (ITEM)", "PRECIO DE VENTA (ITEM)", "CANTIDAD (ITEM)"]
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
    if prod is not None and not prod.isDisable():
        # add product to data dict
        if prod.getCode() in prodDict:
            raise Exception("Key must be unique")
        prodDict[prod.getCode()]=prod

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
        'MCup', 'MCups', 'SUGERIDO', 'FF', 'GEN' ]

outMed_df = pandas.DataFrame(dataMeds, columns = cols)
outOther_df = pandas.DataFrame(dataOther, columns = cols)
outPack_df = pandas.DataFrame(dataPack, columns = cols)

now = datetime.now().strftime("%Y%m%d")
excel_name = 'PriceSetup_'+now+'.xlsx'

with pandas.ExcelWriter(excel_name) as excel_writer:
    outMed_df.to_excel(excel_writer, sheet_name='Medicamentos', index=False)
    outOther_df.to_excel(excel_writer, sheet_name='Otros', index=False)
    outPack_df.to_excel(excel_writer, sheet_name='Paquetes', index=False)


cols2 = ["CÓDIGO", "NOMBRE", "ALIAS", "UNIDAD", "PRECIO DE VENTA", "PRECIO DE COMPRA", "CANTIDAD",
        "num_regsan (EXTRA)", "lab (EXTRA)", "disable (EXTRA)", "creado (EXTRA)", "generico (EXTRA)", "fecha_vto (EXTRA)",
        "nro_lote (EXTRA)", "adicional (EXTRA)", "otc (EXTRA)", "temp_alm (EXTRA)", "units_blister (EXTRA)",
        "units_caja (EXTRA)", "MONEDA DE VENTA", "MONEDA DE COMPRA", "CON STOCK", "CATEGORÍA",
        "IMPUESTO", "PESO BRUTO (KGM)", "STOCK MÍNIMO", "PORCENTAJE DE GANANCIA", "DESCUENTO", "TIPO DE DESCUENTO",
        "BÚSQUEDA DESDE VENTAS", "CATEGORÍA SUNAT"
        ]


import_prods = createDataListToImport(medsDict)
import_df = pandas.DataFrame(import_prods, columns = cols2)

excel_name = 'PriceToImport_'+now+'.xlsx'
with pandas.ExcelWriter(excel_name) as excel_writer:
    import_df.to_excel(excel_writer, index=False)

cols3 = [ "CÓDIGO", "NOMBRE", "ALIAS", "UNIDAD", "PRECIO DE VENTA", "CATEGORÍA", "CÓDIGO (ITEM)", "NOMBRE (ITEM)",
          "ALIAS (ITEM)", "UNIDAD (ITEM)", "PRECIO DE VENTA (ITEM)", "CANTIDAD (ITEM)"
    ]

import_pack = createDataListToImportPack(medsDict, packDict)
importpk_df = pandas.DataFrame(import_pack, columns = cols3)
excel_name = 'PriceToImportPack_'+now+'.xlsx'
with pandas.ExcelWriter(excel_name) as excel_writer:
    importpk_df.to_excel(excel_writer, index=False)