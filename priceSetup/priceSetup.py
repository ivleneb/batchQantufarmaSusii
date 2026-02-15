import sys #, os
sys.path.append(r'../')
from lib.QantuPackage import QantuPackage
from lib.QantuProduct import QantuProduct
from lib.PriceManager import PriceManager
from lib.QantuConfiguration import QantuConfiguration
from lib.SusiiProductLoader import SusiiProductLoader
import pandas
from datetime import datetime

# load configuration
config = QantuConfiguration()
# business id
business_ = config.business_


colCosto = 'D'
colPrecio = 'E'
colMargen = 'F'
colMargenx = 'H'

igv = 0.18
igvC = 1-igv

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
            prod.getPrice(), round(prod.getLastCost(), 3), prod.getStock(), prod.getNumRegSan(),
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
        
        if prod.getPriceLogic()<1.0:
            print("WARN Product price logic off "+prod.getName())
            continue
        
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

def run():

    loader = SusiiProductLoader(business_)

    # load products from q1
    productDict:dict[str, QantuProduct] = loader.downloadProducts()
    if not productDict:
        print("Fail to downloadProducts.")
        sys.exit(2)

    # load products from q1
    packageDict:dict[str, QantuPackage] = loader.downloadPackages()
    if not packageDict:
        print("Fail to downloadPackages.")
        sys.exit(3)

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