import sys
sys.path.append(r'../')
#from lib.libclass import *
from lib.QantuProduct import QantuProduct
from lib.QantuPackage import QantuPackage
from lib.QantuMedicine import QantuMedicine
from lib.QantuGalenico import QantuGalenico
from lib.QantuDevice import QantuDevice
from lib.QantuGeneral import QantuGeneral
from lib.PriceManager import PriceManager
from lib.ReportDownloader import ReportDownloader
import pandas
from datetime import datetime
import json

# Read JSON file
with open('../lib/cfg.json', 'r', encoding='utf-8') as file:
    cfgData = json.load(file)
    business_ = cfgData["businessId"]

productsDict: dict[str, QantuProduct] = {}
packageDict: dict[str, QantuPackage] = {}

def getProduct(df, code):
    sub_df = df.loc[df['CÓDIGO'] == code]
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
    

def getPackage(prodDict, pack_df, code):
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

    for key, prod in prodDict.items():
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

def isNumeric(col, df):
    if col in df.columns:
        es_numerica = pandas.api.types.is_numeric_dtype(df[col])
        return es_numerica
    else:
        return False
    

def run():
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

    if not isNumeric('generico (EXTRA)', prod_df):
        print("Columna 'generico (EXTRA)' tiene valores no numéricos.")
        sys.exit(1)

    if not isNumeric('units_blister (EXTRA)', prod_df):
        print("Columna 'units_blister (EXTRA)' tiene valores no numéricos.")
        sys.exit(2)
    else:
        prod_df["units_blister (EXTRA)"] = prod_df["units_blister (EXTRA)"].fillna(0)

    if not isNumeric('units_caja (EXTRA)', prod_df):
        print("Columna 'units_caja (EXTRA)' tiene valores no numéricos.")
        sys.exit(3)
    else:
        prod_df['units_caja (EXTRA)'] = prod_df['units_caja (EXTRA)'].fillna(0)

    print("REG SIZE (prod):"+str(len(prod_df)))

    pack_df = pandas.read_excel(file_pack, skiprows=4)
    print("REG SIZE (prod):"+str(len(prod_df)))

    # Load products
    for index, row in prod_df.iterrows():
        # only add sales that are products
        prod = getProduct(prod_df, row['CÓDIGO'])
        if prod is not None and not prod.isDisable():
            # add product to data dict
            if prod.getCode() in productsDict:
                raise Exception("Index["+str(index)+"] Key must be unique")
            productsDict[prod.getCode()]=prod

    # Load packages
    for key, row in pack_df.iterrows():
        # only add sales that are products
        pack = getPackage(productsDict, pack_df, row['CÓDIGO'])
        if pack is not None:
            packageDict[pack.getCode()]=pack
        else:
            print("WARN Key["+str(key)+"] pack is None.")

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