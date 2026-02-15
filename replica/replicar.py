import sys
sys.path.append(r'../')
from lib.QantuProduct import QantuProduct
from lib.QantuConfiguration import QantuConfiguration
from datetime import datetime
from lib.SusiiProductLoader import SusiiProductLoader
import pandas

cobian = 5053
# load configuration
config = QantuConfiguration()
# business id
business_ = config.business_
if business_ == cobian:
    print("FATAL invalid business "+str(business_)+" must be different than COBIAN (Q1)")
    sys.exit(1)

def generateImportFile(impList):
    data = []
    count = 0

    for prod in impList:
        count = count + 1
        
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
    
    
    cols2 = ["CÓDIGO", "NOMBRE", "ALIAS", "UNIDAD", "PRECIO DE VENTA", "PRECIO DE COMPRA", "CANTIDAD",
            "num_regsan (EXTRA)", "lab (EXTRA)", "disable (EXTRA)", "creado (EXTRA)", "generico (EXTRA)", "fecha_vto (EXTRA)",
            "nro_lote (EXTRA)", "adicional (EXTRA)", "otc (EXTRA)", "temp_alm (EXTRA)", "units_blister (EXTRA)",
            "units_caja (EXTRA)", "tipo_tratamiento (EXTRA)", "price_logic (EXTRA)", "seg_1 (EXTRA)", "seg_2 (EXTRA)", "seg_3 (EXTRA)",
            "MONEDA DE VENTA", "MONEDA DE COMPRA", "CON STOCK", "CATEGORÍA",
            "IMPUESTO", "PESO BRUTO (KGM)", "STOCK MÍNIMO", "PORCENTAJE DE GANANCIA", "DESCUENTO", "TIPO DE DESCUENTO",
            "BÚSQUEDA DESDE VENTAS", "CATEGORÍA SUNAT"
            ]


    import_df = pandas.DataFrame(data, columns = cols2)
    now = datetime.now().strftime("%Y%m%d")
    excel_name = str(business_)+'_Replica_'+now+'.xlsx'
    with pandas.ExcelWriter(excel_name) as excel_writer:
        import_df.to_excel(excel_writer, index=False)

def run():
    loader = SusiiProductLoader(cobian)

    # load products from q1
    productDict:dict[str, QantuProduct] = loader.downloadProducts()
    if not productDict:
        print("Fail to downloadProducts.")
        sys.exit(2)

    # load products from q2
    loader.setBusinessId(business_)
    productDictOther:dict[str, QantuProduct] = loader.downloadProducts()
    if not productDictOther:
        print("Fail to downloadProducts from OTHER.")
        sys.exit(3)
    
    impList = []
    # for p1 in products of q1
    for prodCode in productDict:
        # if product exist in the other store
        if prodCode in productDictOther:
            # copy values from main (q1) to other store
            prod = productDictOther[prodCode]
            prodBase = productDict[prodCode]
            prod.setName(prodBase.getName())
            prod.setCategory(prodBase.getCategory())
            prod.setBrand(prodBase.getBrand())
            prod.setPriceLogic(prodBase.getPriceLogic())
            prod.setTipoTratamiento(prodBase.getTipoTratamiento())
            prod.setUnitsBlister(prodBase.getUnitsBlister())
            prod.setUnitsCaja(prodBase.getUnitsCaja())
            prod.setOtc(prodBase.getOtc())
            prod.setSeg1(prodBase.getSeg1())
            prod.setSeg2(prodBase.getSeg2())
            prod.setSeg3(prodBase.getSeg3())
            
            if pandas.isna(prod.getGenerico()):
                prod.setGenerico(prodBase.getGenerico())
            
            if len(prod.getNroLote())>0 and prod.getNroLote()==prodBase.getNroLote():
                prod.setFechaVto(prodBase.getFechaVto())
                prod.setNumRegSan(prodBase.getNumRegSan())
                
            impList.append(prod)
    
    generateImportFile(impList)

run()