import sys
sys.path.append(r'../')
from lib.libclass import *
from lib.ReportDownloader import *
import pandas
from datetime import datetime

# Read JSON file
with open('../lib/cfg.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
    business_ = data["businessId"]

prodDict = {}
packDict = {}

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


"""def computeMCpercent(prod):
    mcu = prod.getPrice()-prod.getLastCost()
    mcup = 100*(mcu/prod.getPrice())
    return round(mcup, 2)

def computePriceBlister(prod):
    mcup = computeMCpercent(prod)
    
    
def computePriceCja():
"""

def createPackageBlister(prod):
    cantidadItemBlis = int(prod.getUnitsBlister())
    packPrice = round(prod.getPrice()*cantidadItemBlis*0.7, 1)
    packName = "Blister "+prod.getName()+"X"+str(cantidadItemBlis)
    ls = [ prod.getCode()+"BLI"+str(cantidadItemBlis), packName, "", "UNIDAD",
        packPrice,  prod.getCategory(), prod.getCode(), prod.getName(),
        "", prod.getUnidad(), prod.getPrice(), cantidadItemBlis
    ]
    print("NUEVO BLISTER: ")
    print(ls)
    return ls

def createPackageCja(prod):
    cantidadItemCja = int(prod.getUnitsCaja())
    packPrice = round(prod.getPrice()*cantidadItemCja*0.5, 1)
    packName = "Cja "+prod.getName()+"X"+str(cantidadItemCja)
    ls = [ prod.getCode()+"CJA"+str(cantidadItemCja), packName, "", "UNIDAD",
        packPrice,  prod.getCategory(), prod.getCode(), prod.getName(),
        "", prod.getUnidad(), prod.getPrice(), cantidadItemCja
    ]
    print("NUEVA CJA: ")
    print(ls)
    return ls

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
                            # check for type
                            checkPackType(pack, prod)
                        else:
                            print("WARNING PACK["+pack.getName()+"] has more than 1 item.")
                # No pack found
                if not hasPack:
                    print("NO_PACK PROD["+prod.getName()+"] hasn't pack. Create!")
                    # crear blister
                    cantidadItemBlis = int(prod.getUnitsBlister())
                    if cantidadItemBlis == 1:
                        print("WARNING prod["+prod.getName()+"] has unitsBlister["+str(cantidadItemBlis)+"]")
                    else:
                        data.append(createPackageBlister(prod))
                    
                    # crear cja
                    cantidadItemCja = int(prod.getUnitsCaja())
                    if cantidadItemCja == 1:
                        print("WARNING prod["+prod.getName()+"] has unitsCja["+str(cantidadItemCja)+"]")
                    elif cantidadItemCja == cantidadItemBlis:
                        continue
                    else:
                        data.append(createPackageCja(prod))
                    
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

#dataMeds = createDataList(medsDict)
#dataOther = createDataList(otherDict)
#dataPack = createDataListPack(packDict)

now = datetime.now().strftime("%Y%m%d")


cols3 = [ "CÓDIGO", "NOMBRE", "ALIAS", "UNIDAD", "PRECIO DE VENTA", "CATEGORÍA", "CÓDIGO (ITEM)", "NOMBRE (ITEM)",
          "ALIAS (ITEM)", "UNIDAD (ITEM)", "PRECIO DE VENTA (ITEM)", "CANTIDAD (ITEM)"
    ]

import_pack = createDataListToImportPack(medsDict, packDict)
importpk_df = pandas.DataFrame(import_pack, columns = cols3)
excel_name = str(business_)+'_PriceToImportPack_'+now+'.xlsx'
with pandas.ExcelWriter(excel_name) as excel_writer:
    importpk_df.to_excel(excel_writer, index=False)