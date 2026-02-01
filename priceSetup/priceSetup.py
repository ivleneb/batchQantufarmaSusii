import sys #, os
sys.path.append(r'../')
from lib.QantuMedicine import QantuMedicine
from lib.QantuGalenico import QantuGalenico
from lib.QantuDevice import QantuDevice
from lib.QantuGeneral import QantuGeneral
from lib.QantuPackage import QantuPackage
from lib.QantuProduct import QantuProduct
from lib.PriceManager import PriceManager
from lib.ReportDownloader import ReportDownloader
import pandas
from datetime import datetime
import json


# Read JSON file
with open('../lib/cfg.json', 'r', encoding='utf-8') as file:
    cfgData = json.load(file)
    business_ = cfgData["businessId"]


colCosto = 'D'
colPrecio = 'E'
colMargen = 'F'
colMargenx = 'H'

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
        prod.setTipoTratamiento(row["tipo_tratamiento (EXTRA)"])
        prod.setPriceLogic(row["price_logic (EXTRA)"])
        prod.setSeg1(row["seg_1 (EXTRA)"])
        prod.setSeg2(row["seg_2 (EXTRA)"])
        prod.setSeg3(row["seg_3 (EXTRA)"])
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
                print(f"WARN index={index} Package {code}[{pName}] item not found {codeItem}")
            
        pack.setCost(cost)
        return pack
    else:
        #print(f"Package {code} not found, invalid or deleted")
        return None

def createDataList(prodDict):
    data = []
    count = 0

    for prod in prodDict.values():
        count = count + 1
        mcu = '={colP}{rowP}-{colC}{rowC}'.format(colP=colPrecio, rowP=count+1,
                                                  colC=colCosto, rowC=count+1)
        mcup = '= {colM}{rowM}/{colP}{rowP}'.format(colM=colMargen, rowM=count+1,
                                                    colP=colPrecio, rowP=count+1)
        
        mcups = '0'
        
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

    for pack in packDict.values():
        count = count + 1
        mcu = '={colP}{rowP}-{colC}{rowC}'.format(colP=colPrecio, rowP=count+1,
                                                  colC=colCosto, rowC=count+1)
        mcup = '= {colM}{rowM}/{colP}{rowP}'.format(colM=colMargen, rowM=count+1,
                                                    colP=colPrecio, rowP=count+1)
        mcups = "0"
        if pack.getCategory()=='MEDICAMENTOS' and pack.isGenerico():
            mcups_r = 0.35
            mcups = '='+str(mcups_r)
            #forma_far = pack.itemsObj[].getFF()
            #is_gen = pack.isGenerico()
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

    for prod in prodDict.values():
        count = count + 1
        
        #mcups = 0
        price = None
        
        if prod.getPriceLogic()<1.0:
            print("WARN Product price logic off "+prod.getName())
            continue
        
        if prod.getLastCost()<=0.0:
            print("Prodcut without cost "+prod.getName())
            continue
        
        #if prod.getCategory()=='MEDICAMENTOS':
        #    #mcups = priceMedicamentos(prod)
        #    price = PriceManager.computePrice(prod)
        #else:
            # ignore products
        ls = ['PAPEL', 'PAÑAL']
        ignore = False
        for keyname in ls:
            if keyname in prod.getName():
                ignore = True
                break
        if ignore:
            print("Ignore product "+prod.getName())
            continue
            # general margin
            # mcups = priceGeneral(prod)
        price = PriceManager.computePrice(prod)
        
        gan_per = price.getProfitPer() #(mcups/(1-mcups))
        #gan_per = round(gan_per, 4)
        #prod.setPorcentajeDeGanancia(gan_per*100)
        presug = price.getValue() #round((1+gan_per)*prod.getLastCost(), 1)
        print("precio sugerido:"+str(presug))
        if presug<=prod.getPrice():
            print("Product has a better price than logic "+prod.getName())
            continue
        else:
            prod.setPrice(presug)
            prod.setPorcentajeDeGanancia(gan_per*100)
            
        if presug < 0.5:
            prod.setPrice(0.5)
            prod.setPorcentajeDeGanancia('')
        
        ls = [ prod.getCode(), prod.getName(), prod.getAlias(), prod.getUnidad(),
            prod.getPrice(), prod.getLastCost(), prod.getStock(), prod.getNumRegSan(),
            prod.getBrand(), prod.getDisable(), prod.getCreatedAt(), prod.getGenerico(),
            prod.getFechaVto(), prod.getNroLote(), prod.getAdicional(), prod.getOtc(),
            prod.getTempAlm(), prod.getUnitsBlister(), prod.getUnitsCaja(), prod.getTipoTratamiento(), prod.getPriceLogic(),
            prod.getSeg1(), prod.getSeg2(), prod.getSeg3(),
            prod.getMonedaDeVenta(),
            prod.getMonedaDeCompra(), prod.getConStock(), prod.getCategory(),  prod.getImpuesto(),
            prod.getPesoBruto(), prod.getMinStock(), prod.getPorcentajeDeGanancia(), prod.getDescuento(),
            prod.getTipoDeDescuento(), prod.getBusquedaDesdeVentas(), prod.getCategoriaSunat()
        ]
        
        data.append(ls)
    return data

def createDataListToImportPack(prodDict, packDict):
    data = []
    count = 0

    for prod in prodDict.values():
        count = count + 1

        #if prod.getCategory()=='MEDICAMENTOS' and prod.isGenerico():
        #if prod.getCategory()=='MEDICAMENTOS':
            #if prod.getFF() in ['TAB']:
        #hasPack=False
        for pack in packDict.values():
            if prod.getCode() in pack.itemsObj :
                if len(pack.itemsObj)==1:
                    #hasPack=True
                    print("PROD["+prod.getName()+"] already has pack["+pack.getName()+"].")
                    nbr = pack.getItems()[prod.getCode()]
                    price = None
                    if nbr == prod.getUnitsBlister():
                        price = PriceManager.computeProductBlisterPrice(prod)
                    elif nbr == prod.getUnitsCaja():
                        price = PriceManager.computeProductCajaPrice(prod)
                    else:
                        print("ERROR package nbr of items not equal to unitsCaja nor unitsBlister.")
                        break
                    
                    if price is None:
                        print("ERROR compute price end with error.")
                        break
                    
                    value = price.getValue()
                    if pack.getPrice()<value:
                        pack.setPrice(value)
                        cantidadItem = pack.items[prod.getCode()]
                        ls = [ pack.getCode(), pack.getName(), pack.getAlias(), pack.getUnidad(),
                            pack.getPrice(),  pack.getCategory(), prod.getCode(), prod.getName(),
                            prod.getAlias(), prod.getUnidad(), prod.getPrice(), cantidadItem
                        ]  
                    
                        data.append(ls)
                    else:
                        print("WARN current price of pack is better "+pack.getName())
                else:
                    print("PACK["+pack.getName()+"] has more than 1 item.")
            #else:
            #    continue
        #else:
        #    continue
    return data

def isNumeric(col, df):
    if col in df.columns:
        es_numerica = pandas.api.types.is_numeric_dtype(df[col])
        return es_numerica
    else:
        return False
    
def validateProductDf(prod_df):
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
    
    if not isNumeric("price_logic (EXTRA)", prod_df):
        print("Columna 'price_logic (EXTRA)' tiene valores no numéricos.")
        sys.exit(4)
    else:
        prod_df["price_logic (EXTRA)"] = prod_df["price_logic (EXTRA)"].fillna(1)

def run():
    productDict:dict[str, QantuProduct] = {}
    packageDict:dict[str, QantuPackage] = {}
    today = datetime.now().strftime("%Y-%m-%d")

    # download product data
    repHeaders = ["CÓDIGO", "NOMBRE", "ALIAS", "UNIDAD", "PRECIO DE VENTA", "PRECIO DE COMPRA", "CANTIDAD",
            "num_regsan (EXTRA)", "lab (EXTRA)", "disable (EXTRA)", "creado (EXTRA)", "generico (EXTRA)", "fecha_vto (EXTRA)",
            "nro_lote (EXTRA)", "adicional (EXTRA)", "otc (EXTRA)", "temp_alm (EXTRA)", "units_blister (EXTRA)",
            "units_caja (EXTRA)", "tipo_tratamiento (EXTRA)", "price_logic (EXTRA)", "seg_1 (EXTRA)", "seg_2 (EXTRA)", "seg_3 (EXTRA)",
            "MONEDA DE VENTA", "MONEDA DE COMPRA", "CON STOCK", "CATEGORÍA",
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

    validateProductDf(prod_df)

    pack_df = pandas.read_excel(file_pack, skiprows=4)
    print("REG SIZE (prod):"+str(len(prod_df)))

    # Load products
    for index, row in prod_df.iterrows():
        # only add sales that are products
        prod = getProduct(prod_df, row['CÓDIGO'])
        if prod is not None and not prod.isDisable():
            # add product to data dict
            if prod.getCode() in productDict:
                raise Exception("FATAL Index["+str(index)+"] Key must be unique")
            productDict[prod.getCode()]=prod
            
    # Load packages
    for key, row in pack_df.iterrows():
        # only add sales that are products
        pack = getPackage(productDict, pack_df, row['CÓDIGO'])
        if pack is not None:
            packageDict[pack.getCode()]=pack


    medsDict = {}
    otherDict = {}
    for key, prod in productDict.items():
        if prod.getCategory()=='MEDICAMENTOS':
            medsDict[key]=prod
        else:
            otherDict[key]=prod

    dataMeds = createDataList(medsDict)
    dataOther = createDataList(otherDict)
    dataPack = createDataListPack(packageDict)
        
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
            "units_caja (EXTRA)", "tipo_tratamiento (EXTRA)", "price_logic (EXTRA)", "seg_1 (EXTRA)", "seg_2 (EXTRA)", "seg_3 (EXTRA)",
            "MONEDA DE VENTA", "MONEDA DE COMPRA", "CON STOCK", "CATEGORÍA",
            "IMPUESTO", "PESO BRUTO (KGM)", "STOCK MÍNIMO", "PORCENTAJE DE GANANCIA", "DESCUENTO", "TIPO DE DESCUENTO",
            "BÚSQUEDA DESDE VENTAS", "CATEGORÍA SUNAT"
            ]


    import_prods = createDataListToImport(medsDict)
    import_df = pandas.DataFrame(import_prods, columns = cols2)

    excel_name = str(business_)+'_PriceToImportMeds_'+now+'.xlsx'
    with pandas.ExcelWriter(excel_name) as excel_writer:
        import_df.to_excel(excel_writer, index=False)
        
    
    import_prods = createDataListToImport(otherDict)
    import_df = pandas.DataFrame(import_prods, columns = cols2)

    excel_name = str(business_)+'_PriceToImportOther_'+now+'.xlsx'
    with pandas.ExcelWriter(excel_name) as excel_writer:
        import_df.to_excel(excel_writer, index=False)

    cols3 = [ "CÓDIGO", "NOMBRE", "ALIAS", "UNIDAD", "PRECIO DE VENTA", "CATEGORÍA", "CÓDIGO (ITEM)", "NOMBRE (ITEM)",
              "ALIAS (ITEM)", "UNIDAD (ITEM)", "PRECIO DE VENTA (ITEM)", "CANTIDAD (ITEM)"
        ]

    import_pack = createDataListToImportPack(productDict, packageDict)
    importpk_df = pandas.DataFrame(import_pack, columns = cols3)
    excel_name = str(business_)+'_PriceToImportPack_'+now+'.xlsx'
    with pandas.ExcelWriter(excel_name) as excel_writer:
        importpk_df.to_excel(excel_writer, index=False)


run()