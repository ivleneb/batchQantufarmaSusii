import sys
sys.path.append(r'../')
from lib.QantuProduct import QantuProduct
from lib.QantuMergedProduct import QantuMergedProduct
from lib.QantuPackage import QantuPackage
from lib.QantuProductMerger import QantuProductMerger
from lib.QantuConfiguration import QantuConfiguration
from datetime import datetime
from lib.SusiiProductLoader import SusiiProductLoader
from lib.BatchUtils import BatchUtils
import pandas
import math

otherBusiness = 8132
lazaro = 8132
cobian = 5053
# load configuration
config = QantuConfiguration()
NBR_DAYS = 4
# business id
business_ = config.business_
if business_ == cobian:
    otherBusiness = lazaro
elif business_ == lazaro:
    otherBusiness = cobian
else:
    print("FATAL invalid business "+str(business_))
    sys.exit(1)

def generateReport(moveList):
    cols3 = [ "CÓDIGO", "NOMBRE", "CANTIDAD"]
    move_df = pandas.DataFrame(moveList, columns = cols3)
    now = datetime.now().strftime("%Y%m%d")
    excel_name = str(business_)+'_ToMoveFrom'+str(otherBusiness)+'_'+now+'.xlsx'
    out_path = './out'
    BatchUtils.crear_carpeta_si_no_existe(out_path)
    fullpath = out_path+'/'+excel_name
    with pandas.ExcelWriter(fullpath) as excel_writer:
        move_df.to_excel(excel_writer, index=False)

def computeTimeWindowDays():
    timeWindow = config.getTimeWindowForBusiness(business_)
    timeWindowDays = timeWindow*30
    startDate = config.getStartDateForBusiness(business_)
    delta = datetime.now() - datetime.strptime(startDate, "%Y-%m-%d")
    
    if delta.days>timeWindowDays:
        return timeWindowDays
    else:
        return delta.days
    
def cargarProductosOrigen():
    loader = SusiiProductLoader(business_)
    productDict: dict[str, QantuProduct] = loader.downloadProducts(downloadSaleData=True, includeDisable=True)
    if not productDict:
        print("Fail to downloadProducts.")
        sys.exit(2)
    return loader, productDict

def cargarProductosOtraSede(loader):
    loader.setBusinessId(otherBusiness)
    productDictOther: dict[str, QantuProduct] = loader.downloadProducts()
    if not productDictOther:
        print("Fail to downloadProducts from OTHER.")
        sys.exit(3)
    return productDictOther

def cargarPaquetesOrigen(loader):
    packDict: dict[str, QantuPackage] = loader.downloadPackages(downloadSaleData=True)
    if not packDict:
        print("Fail to downloadPackages.")
        sys.exit(4)
    return packDict

def actualizarVentasPorPaquetes(productDict, packDict):
    print("First product filter")
    for pack in packDict.values():
        for packprodCode, qty in pack.getItems().items():
            if packprodCode in productDict:
                productDict[packprodCode].addSoldUnits(qty * pack.getSoldUnits())
    return productDict

## Caso Especial Prod GOLD (isGenerico()=2).
def buscarProductosEquivalentes(prod, productDictOther):
    productosEquivalentes = []
    for prodOther in productDictOther.values():
        if prod.getCode() == prodOther.getCode():
            productosEquivalentes.append(prodOther)
        elif prod.getName() == prodOther.getName():
            productosEquivalentes.append(prodOther)
    return productosEquivalentes

def obtenerStockTotalEquivalente(productosEquivalentes):
    stockTotal = 0
    for prodOther in productosEquivalentes:
        stockTotal += prodOther.getStock()
    return stockTotal

def procesarProductoGold(prod, productDictOther, moveList):
    productosEquivalentes = buscarProductosEquivalentes(prod, productDictOther)
    if not productosEquivalentes:
        print("GOLD [" + prod.getName() + "] NOT in OTHER store.")
        return
    stockActual = prod.getStock()
    minStockActual = prod.getMinStock()
    stockOtroLocal = obtenerStockTotalEquivalente(productosEquivalentes)
    # Si ya tiene más del doble de su stock mínimo, no pedir
    if stockActual > minStockActual * 2:
        print("GOLD [" + prod.getName() +"] tiene stock suficiente.")
        return
    # Stock total entre ambas sedes
    stockTotal = stockActual + stockOtroLocal
    # Cuánto necesitaría para quedar equilibrado
    stockEquilibrado = stockTotal / 2
    cantidadSolicitada = math.floor(stockEquilibrado - stockActual)
    if cantidadSolicitada <= 0:
        print("GOLD [" + prod.getName() +"] no requiere traslado.")
        return
    # Determinar el stock mínimo que debemos dejar en la otra sede
    minStockOtroLocal = 0
    for prodOther in productosEquivalentes:
        minStockOtroLocal += prodOther.getMinStock()
    # Cuánto puede entregar realmente la otra sede
    disponibleParaTraslado = (stockOtroLocal - minStockOtroLocal)
    if disponibleParaTraslado <= 0:
        print("GOLD [" + prod.getName() +"] OTHER store no tiene excedente.")
        return
    # Nunca trasladar más de lo necesario ni más de lo que realmente puede entregar la otra sede
    cantidadTraslado = min(cantidadSolicitada, disponibleParaTraslado)
    # Caso Productos que vienen en Blister
    if prod.getUnitsBlister() > 1:
        cantidadBlister = cantidadTraslado // prod.getUnitsBlister()
        TrasladoBlister = cantidadBlister * prod.getUnitsBlister()
        if cantidadBlister < 1:
            print("GOLD ["+prod.getName()+"] OTHER store no tiene suficiente para enviar blister")
            return 0
        moveList.append([prod.getCode(), prod.getMergedName(), TrasladoBlister])
        return
    #Traslado
    if cantidadTraslado > 0:
        print("GOLD [" + prod.getName() + "] Trasladar " + str(cantidadTraslado) + " unidades.")
        moveList.append([prod.getCode(), prod.getMergedName(), cantidadTraslado])
##Fin de Prod GOLD.

def calcularNecesidadProducto(prod, timeWindowDays):
    active_days = prod.getActiveDays()
    if active_days == 0:
        print("Active days is 0, default to 1")
        active_days = 1
    if timeWindowDays < active_days:
        active_days = timeWindowDays
    stock = prod.getStock()
    daily_mean = prod.getSoldUnits() / active_days
    requestQtty = NBR_DAYS * daily_mean - stock
    return stock, requestQtty

def procesarProductoNecesitado(prod, prodCode, productDictOther, stock, requestQtty, moveList):
    ## Caso de si el producto es considerado GOLD.
    if prod.getGenerico() == 2:
        procesarProductoGold(prod, productDictOther, moveList)
        return
    if requestQtty > 0.5 * stock:
        requestQtty = math.ceil(requestQtty)
        print("Prod["+prod.getName()+"] require units.")
        # Si el producto existe en la otra sede
        if prodCode in productDictOther:
            prod2 = productDictOther[prodCode]
            # Producto sin blister o con blister de 1 unidad
            if (prod2.getUnitsBlister() == 1 or prod2.getUnitsBlister() == 0):
                diff_stock = abs(stock - prod2.getStock())
                if diff_stock < 3 and stock != 0:
                    print("No trasladar, stock similar.")
                    return
                max_available = math.floor(prod2.getStock() * 0.5)
                if max_available > requestQtty:
                    print("Trasladar!")
                    moveList.append([prod.getCode(), prod.getMergedName(), requestQtty])
                elif max_available > 0:
                    print("Trasladar!")
                    moveList.append([prod.getCode(), prod.getMergedName(), max_available])
            elif (prod2.getUnitsBlister() > 0 and prod2.getStock() > prod2.getUnitsBlister()):
                print("Trasladar!")
                moveList.append([prod.getCode(), prod.getMergedName(), prod2.getUnitsBlister()])
            elif (prod2.getUnitsCaja() > 0 and prod2.getStock() > prod2.getUnitsCaja()):
                print("Trasladar!")
                moveList.append([prod.getCode(), prod.getMergedName(), prod2.getUnitsCaja()])
            else:
                print("Prod [" + prod2.getName() + "] Check units blister or units cja.")
        else:
            print("Prod[" + prod.getName() + "] NOT in OTHER store.")
            
def procesarProductoOficina(prod, prodCode, productDictOther, moveList):
    if (prod.getStock() <= 0 and prod.getCode() in productDictOther
        and any(elem in prod.getName() for elem in ['BOLSA', 'CINTA'])):
        prod2 = productDictOther[prodCode]
        if prod2.getStock() < 2:
            return
        if (prod2.getUnitsCaja() > 1 and prod2.getStock() * 0.5 > prod2.getUnitsCaja()):
            moveList.append([prod.getCode(), prod.getName(), prod2.getUnitsCaja()])
        else:
            moveList.append([prod.getCode(), prod.getName(), 1])
            
def existeEquivalenteEnDestino(prod2, productDict):
    # Si es un producto combinado
    if isinstance(prod2, QantuMergedProduct):
        skip = False
        for codeInner in prod2.products:
            try:
                print("Element [" + codeInner + "]" + prod2.products[codeInner].getName())
            except TypeError:
                print(type(codeInner))
                print(codeInner.__class__)
            if codeInner in productDict:
                print("Element [" + codeInner + "]" + prod2.products[codeInner].getName() +
                      " exists in destiny DB.")
                skip = True
                break
            else:
                for codeOrigin in productDict:
                    if(prod2.products[codeInner].getName() == productDict[codeOrigin].getName()):
                        print("Element [" + codeInner + "]" + prod2.products[codeInner].getName() +
                            " has equivalente in destiny DB.")
                        skip = True
                        break
                if skip == True:
                    break
        return skip
    # Si no es combinado, revisar código funcional
    elif prod2.functionalCode() in productDict:
        print("Element [" + prod2.getCode() + "]" + prod2.getName() + " has equivalent in destiny DB.")
        return True
    # Los productos de OFICINA se omiten
    elif prod2.getCategory() == 'OFICINA':
        return True
    # Comparación con productos existentes
    else:
        skip = False
        for prodCodeX in productDict:
            prodX = productDict[prodCodeX]
            words = [
                "PAPEL",
                "PAÑUELO",
                "SACHET",
                "DESODORANTE",
                "REGALO"
            ]
            if prod2.functionalCode() == prodX.functionalCode():
                print("Element [" + prod2.getCode() + "]" + prod2.getName() +
                    " has equivalent in destiny DB (" + prodX.getCode() + ").")
                skip = True
                break
            elif prod2.getName() == prodX.getName():
                print("Element [" + prod2.getCode() + "]" + prod2.getName() +
                    " has equivalent in destiny DB (" + prodX.getName() + ").")
                skip = True
                break
            elif any(w in prod2.getName() for w in words):
                print("Element [" + prod2.getCode() + "]" + prod2.getName() + " has banned from traslados")
                skip = True
                break
        return skip

def procesarMedicamentoNuevo(prod2, business_, moveList):
    if prod2.getUnitsBlister() > 0 and prod2.getStock() > prod2.getUnitsBlister():
        print("PROD [" + prod2.getCode() + "]" + prod2.getName() + " no existe en " + str(business_))
        if isinstance(prod2, QantuMergedProduct):
            print("IS QantuMergedProduct " + prod2.getCode())
        print("Trasladar!")
        moveList.append([prod2.getCode(), prod2.getMergedName(), prod2.getUnitsBlister()])
    elif prod2.getUnitsCaja() > 0 and prod2.getStock() > prod2.getUnitsCaja():
        print("PROD [" + prod2.getCode() + "]" + prod2.getName() + " no existe en " + str(business_))
        if isinstance(prod2, QantuMergedProduct):
            print("IS QantuMergedProduct " + prod2.getCode())
        print("Trasladar!")
        moveList.append([prod2.getCode(), prod2.getMergedName(), prod2.getUnitsCaja()])
    else:
        print("Prod [" + prod2.getName() + "] Check units blister or units cja.")

def procesarProductoNuevoNoMedicamento(prod2, business_, moveList):
    if prod2.getStock() > 1:
        print("PROD " + prod2.getName() + " no existe en " + str(business_))
        print("Trasladar!")
        if isinstance(prod2, QantuMergedProduct):
            print("IS QantuMergedProduct " + prod2.getCode())
        moveList.append([prod2.getCode(), prod2.getName(), 1])
    else:
        print("There is not enough stock.")

def run():
    # Sede 1
    loader, productDict = cargarProductosOrigen()
    packDict = cargarPaquetesOrigen(loader)
    productDict = actualizarVentasPorPaquetes(productDict, packDict)
    productDict = QantuProductMerger.combineProducts(productDict)
    # Sede 2
    productDictOther = cargarProductosOtraSede(loader)
    productDictOther = QantuProductMerger.combineProducts(productDictOther)
    
    # for p1 in products of q1
    timeWindowDays = computeTimeWindowDays()
    print("DEFAULT TIME WINDOW DAYS: "+str(timeWindowDays))
    moveList = []
    for prodCode in productDict:
        prod = productDict[prodCode]
        if  prod.isDisable():
            continue
        elif prod.getCategory()=='OFICINA':
            procesarProductoOficina(prod, prodCode, productDictOther, moveList)
        else:
            stock, requestQtty = calcularNecesidadProducto(prod, timeWindowDays)
           # if p1.pedirValue>=0 and stock of p1 in q1 is 0
            procesarProductoNecesitado(prod, prodCode, productDictOther, stock, requestQtty, moveList)

    print("\n\nPRODUCTOS NUEVOS-------------------------------------------------------------------")
    for prodCode in productDictOther:
        if not prodCode in productDict:
            prod2 = productDictOther[prodCode]
            # si es combinado revisar si alguno de los elementos existe en el destino
            if existeEquivalenteEnDestino(prod2, productDict):
                continue
            if prod2.getCategory() == 'MEDICAMENTOS':
                procesarMedicamentoNuevo(prod2, business_, moveList)
            elif prod2.getCategory() != 'MEDICAMENTOS':
                procesarProductoNuevoNoMedicamento(prod2, business_, moveList)
    generateReport(moveList)

run() 