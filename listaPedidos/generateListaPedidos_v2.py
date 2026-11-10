import sys
import os
import re
import json
import unicodedata
from pathlib import Path
from datetime import datetime

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import (Font, PatternFill, Alignment, Border, Side)

sys.path.append(r'../')

from lib.QantuProduct import QantuProduct
from lib.QantuPackage import QantuPackage
from lib.QantuConfiguration import QantuConfiguration
from lib.SusiiProductLoader import SusiiProductLoader
from lib.QantuProductMerger import QantuProductMerger


# ============================================================
# CONFIGURACION
# ============================================================
CFG_PATH = Path('../lib/cfg.json').resolve()

def loadCfg():
    with open(CFG_PATH, 'r', encoding='utf-8') as file:
        return json.load(file)

def saveCfg():
    cfg_data["nbrDays"] = NBR_DAYS
    cfg_data["simpleMode"] = simple_mode
    # Siempre desactivado en la configuracion.
    cfg_data["zeroStock"] = False
    with open(CFG_PATH, 'w', encoding='utf-8') as file:
        json.dump(cfg_data, file, indent=4, ensure_ascii=False)
        
def loadCfg():
    with open(CFG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def saveCfg():
    cfg_data["nbrDays"] = NBR_DAYS
    cfg_data["simpleMode"] = simple_mode

    # ZERO_STOCK siempre permanece desactivado en CFG.
    cfg_data["zeroStock"] = False

    with open(CFG_PATH, "w", encoding="utf-8") as file:
        json.dump(cfg_data, file, indent=4, ensure_ascii=False)

cfg_data = loadCfg()

config = QantuConfiguration()

NBR_DAYS = int(cfg_data.get("nbrDays", config.NBR_DAYS))
# ZERO_STOCK no se configura desde el menu.
# Solo se activa temporalmente durante la revision general.
stock_0 = False

business_ = config.business_

simple_mode = bool(cfg_data.get("simpleMode", False))

# Se fuerza zeroStock a false en la configuracion.
if cfg_data.get("zeroStock", False):
    cfg_data["zeroStock"] = False
    saveCfg()


# ============================================================
# COLUMNAS ORIGINALES
# ============================================================

rowProv = 1

colCOD = 'A'
colNOMBRE = 'B'
colCATEGORIA = 'C'
colPA = 'D'
colSTOCK = 'E'
colBRAND = 'F'
colPRVDOR = 'G'
colCOSTO = 'H'
colPRECIO = 'I'
colVENTAS = 'J'
colPER = 'K'
colBLI = 'L'
colCJA = 'M'
colPEDIR = 'N'
colFINAL = 'O'
colCOSTOCJA = 'P'
colTOTAL = 'Q'

FULL_COLUMNS = [
    'COD', 'NOMBRE', 'CATEGORIA', 'PA',
    'STOCK', 'BRAND', 'PRVDOR', 'COSTO',
    'PRECIO', 'VENTAS', 'PER', 'BLI',
    'CJA', 'PEDIR', 'FINAL', 'COSTOCJA', 'MONTO'
]

SIMPLE_COLUMNS = [
    'COD', 'NOMBRE', 'STOCK',
    'CJA', 'FINAL', 'COSTOCJA', 'MONTO'
]

SIMPLE_ALL_COLUMNS = SIMPLE_COLUMNS + ['PRVDOR']


# ============================================================
# UTILIDADES
# ============================================================

def isFF(ls, name):
    for l in ls:
        if l in name:
            return True
    return False


def remove_lab(input_string):
    s = re.sub(r'\[.*?\]', '', input_string)
    return s.strip()


def normalizeText(value):
    if value is None:
        return ""

    text = str(value).strip().casefold()

    text = unicodedata.normalize("NFKD", text)

    return "".join(
        char for char in text
        if not unicodedata.combining(char)
    )


def safeFileName(name):
    name = str(name).strip()
    name = re.sub(r'[\\/*?:"<>|]', '_', name)
    name = re.sub(r'\s+', '_', name)
    return name[:100]


def safeSheetName(name):
    name = re.sub(r'[\\/*?:\[\]]', '_', str(name))
    name = name[:31]

    return name if name else "SIN_PROVEEDOR"


def getNumericValue(value):
    if value is None:
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    value = str(value).strip()

    if value.startswith("="):
        value = value[1:]

    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def getFinalValue(row):
    return getNumericValue(row[14])


def getProductProvider(prod):
    provider = prod.getLastProvider()

    if provider is None or isinstance(provider, float):
        return ""

    return str(provider).strip()


# ============================================================
# FILTROS DE PROVEEDORES DESDE CFG.JSON
# ============================================================

def getProviderFilters():
    return cfg_data.get("providers", {})


def matchesProvider(prod, providerName):
    filters = getProviderFilters()

    aliases = filters.get(providerName, [])

    if not isinstance(aliases, list):
        return False

    realProvider = normalizeText(getProductProvider(prod))

    if not realProvider:
        return False

    for alias in aliases:
        alias = normalizeText(alias)

        if alias and alias in realProvider:
            return True

    return False


def filterProductsByProvider(prodDict, providerName):
    return {
        code: prod
        for code, prod in prodDict.items()
        if matchesProvider(prod, providerName)
    }


def getActualProviderGroups(prodDict):
    groups = {}

    for code, prod in prodDict.items():

        provider = getProductProvider(prod)

        if not provider:
            provider = "SIN_PROVEEDOR"

        if provider not in groups:
            groups[provider] = {}

        groups[provider][code] = prod

    return groups


# ============================================================
# DESCARGA DE PRODUCTOS
# ============================================================

def loadProductAndPackageData():

    loader = SusiiProductLoader(business_)

    prodDict: dict[str, QantuProduct] = (
        loader.downloadProducts(downloadSaleData=True)
    )

    if not prodDict:
        print("Fail to downloadProducts.")
        sys.exit(2)

    packDict: dict[str, QantuPackage] = (
        loader.downloadPackages(downloadSaleData=True)
    )

    if not packDict:
        print("Fail to downloadPackages.")
        sys.exit(3)

    return prodDict, packDict


def increaseSoldUnitsByPackages(prodDict, packDict):

    print("First product filter")

    for pack in packDict.values():

        for packprodCode, qty in pack.getItems().items():

            if packprodCode in prodDict.keys():

                prodDict[packprodCode].addSoldUnits(
                    qty * pack.getSoldUnits()
                )


# ============================================================
# LOGICA ORIGINAL DE CALCULO
# NO MODIFICAR
# ============================================================

def medsCriteria(prod, pedirVal, perVal):

    final = '=0'

    if pedirVal < 0.5:
        return final

    cja = prod.getUnitsCaja()

    if cja == 0 and isFF(["TUB", "FCO"], prod.getName()):
        print("DEFAULT for TUB or FCO is 1 " + prod.getName())
        cja = 1

    elif cja == 0 and isFF(["TAB", "CAP"], prod.getName()):
        print("DEFAULT for TAB or CAP is 30 " + prod.getName())
        cja = 30

    if cja == prod.getCantidad():
        cja = 1

    flag = False

    for i in range(20):

        if cja * (i + 0.25) < pedirVal and cja * (i + 1.25) > pedirVal:

            final = '={val}'.format(val=i + 1)
            flag = True
            break

    if not flag and perVal > 0.5:
        final = '={val}'.format(val=1)

    return final


def bellezaCriteria(prod, pedirVal, perVal):

    final = '=0'

    if prod.getStock() <= 0 and pedirVal < 0.25:
        return final

    cja = prod.getUnitsCaja()

    if cja == 0:
        print("DEFAULT for OTHERS CAT is 1 " + prod.getName())
        cja = 1

    flag = False

    for i in range(20):

        if cja * (i + 0.25) < pedirVal and cja * (i + 1.25) > pedirVal:

            final = '={val}'.format(val=i + 1)
            flag = True
            break

    if not flag and perVal >= 0.25:
        final = '={val}'.format(val=1)

    return final


def defaultCriteria(prod, pedirVal, perVal):

    final = '=0'

    if prod.getStock() <= 0 and pedirVal < 0.25:
        return final

    cja = prod.getUnitsCaja()

    if cja == 0:
        print("DEFAULT for OTHERS CAT is 1 " + prod.getName())
        cja = 1

    flag = False

    for i in range(20):

        if cja * (i + 0.25) < pedirVal and cja * (i + 1.25) > pedirVal:

            final = '={val}'.format(val=i + 1)
            flag = True
            break

    if not flag and perVal >= 0.25:
        final = '={val}'.format(val=1)

    return final


def computeTimeWindowDays():

    timeWindow = config.getTimeWindowForBusiness(business_)

    timeWindowDays = timeWindow * 30

    startDate = config.getStartDateForBusiness(business_)

    delta = datetime.now() - datetime.strptime(
        startDate, "%Y-%m-%d"
    )

    if delta.days > timeWindowDays:
        return timeWindowDays
    else:
        return delta.days


# Caso GOLD
def goldNeedsMandatoryOrder(prod):

    minStock = prod.getMinStock()
    stock = prod.getStock()

    if minStock <= 0:
        return False

    # Si llegó al mínimo o está por debajo, pedir obligatoriamente
    return stock <= minStock


def calculateOrderData(prod, count, timeWindowDays):

    if stock_0:
        prod.setStock(0)

    if prod.getStock() == 0:
        per = '=100'

    active_days = prod.getActiveDays()

    if active_days == 0:
        active_days = 1

    if timeWindowDays < active_days:
        active_days = timeWindowDays

    pedir = '=({dys}*{colV}{rowV}/{n})-{colS}{rowS}'.format(
        dys=NBR_DAYS,
        n=active_days,
        colV=colVENTAS,
        rowV=count + 1,
        colS=colSTOCK,
        rowS=count + 1
    )

    per = '= {colP}{rowP}/ABS({colS}{rowS})'.format(
        colP=colPEDIR,
        rowP=count + 1,
        colS=colSTOCK,
        rowS=count + 1
    )

    daily_mean = prod.getSoldUnits() / active_days

    pedirVal = (NBR_DAYS * daily_mean - prod.getStock())

    if active_days < NBR_DAYS:

        pedirVal = (active_days * daily_mean - prod.getStock())

        print("LESS THAN " + str(NBR_DAYS) + " days " + prod.getName())

        pedir = '={pedirValue}'.format(
            pedirValue=pedirVal
        )

    perVal = 0

    if prod.getStock() != 0:
        perVal = pedirVal / prod.getStock()
    else:
        perVal = 1000

    return pedir, per, pedirVal, perVal


def determineFinalOrder(prod, pedirVal, perVal):

    final = '0'
    finalGold = '0'

    # Normal
    if prod.getCategory() == 'MEDICAMENTOS':
        final = medsCriteria(prod, pedirVal, perVal)

    elif prod.getCategory() == 'BELLEZA':
        final = bellezaCriteria(prod, pedirVal, perVal)

    else:
        final = defaultCriteria(prod, pedirVal, perVal)

    # GOLD
    if prod.getGenerico() == 2 and goldNeedsMandatoryOrder(prod):

        if prod.getUnitsCaja() < 10:
            finalGold = f"={prod.getMinStock()}"
        else:
            # Si la caja es mas grande, basta que se pida 1 como minimo
            finalGold = "=1"

    # Comparar los numeros, se pedira el mas alto.
    val_final = (
        float(final.replace("=", ""))
        if final.startswith("=")
        else float(final)
    )

    val_gold = (
        float(finalGold.replace("=", ""))
        if finalGold.startswith("=")
        else float(finalGold)
    )

    return f"={max(val_final, val_gold)}"


# ============================================================
# COSTOS Y CONSTRUCCION DE FILAS
# ============================================================

def calculateOrderCosts(count):

    priceCja = '={colCostUni}{rowP}*{colCaja}{rowP}'.format(
        colCostUni=colCOSTO,
        colCaja=colCJA,
        rowP=count + 1
    )

    monto = '={colCostUni}{rowP}*{colCaja}{rowP}*{colF}{rowP}'.format(
        colCostUni=colCOSTO,
        colCaja=colCJA,
        colF=colFINAL,
        rowP=count + 1
    )

    return priceCja, monto


def createProductRow(prod, per, pedir, final, priceCja, monto):

    l = []

    if prod.getCategory() == 'MEDICAMENTOS':

        l = [
            prod.getCode(),
            prod.getMergedName(),
            prod.getCategory(),
            prod.getPrincipioActivo(),
            prod.getStock(),
            prod.getBrand(),
            prod.getLastProvider(),
            prod.getLastCost(),
            prod.getPrice(),
            prod.getSoldUnits(),
            per,
            prod.getUnitsBlister(),
            prod.getUnitsCaja(),
            pedir,
            final,
            priceCja,
            monto
        ]

    else:

        l = [
            prod.getCode(),
            prod.getMergedName(),
            prod.getCategory(),
            '',
            prod.getStock(),
            prod.getBrand(),
            prod.getLastProvider(),
            prod.getLastCost(),
            prod.getPrice(),
            prod.getSoldUnits(),
            per,
            0,
            prod.getUnitsCaja(),
            pedir,
            final,
            priceCja,
            monto
        ]

    return l


def registerProvider(prod, providers):

    lastProvider = prod.getLastProvider()

    if lastProvider is None or isinstance(lastProvider, float):
        lastProvider = ""

    if not lastProvider in providers:
        providers.append(lastProvider)


def createDataList(prodDict, providers):

    data = []

    count = 0

    timeWindowDays = computeTimeWindowDays()

    print("DEFAULT TIME WINDOW DAYS: " + str(timeWindowDays))

    for prod in prodDict.values():

        count = count + 1

        pedir, per, pedirVal, perVal = calculateOrderData(
            prod,
            count,
            timeWindowDays
        )

        final = determineFinalOrder(
            prod,
            pedirVal,
            perVal
        )

        priceCja, monto = calculateOrderCosts(count)

        l = createProductRow(
            prod,
            per,
            pedir,
            final,
            priceCja,
            monto
        )

        data.append(l)

        registerProvider(prod, providers)

    return data


# ============================================================
# MODO SIMPLE
# ============================================================

def createSimpleRows(data, includeProvider=False):

    result = []

    for row in data:

        # SIMPLE_MODE omite productos cuyo FINAL sea cero.
        if getFinalValue(row) <= 0:
            continue

        count = len(result) + 2

        code = row[0]
        name = row[1]
        stock = row[4]
        provider = row[6]
        cost = getNumericValue(row[7])
        cja = getNumericValue(row[12])
        final = row[14]

        # COSTOCJA conserva el cálculo original:
        # costo unitario * unidades por caja.
        costCja = cost * cja

        # MONTO = COSTOCJA * FINAL.
        monto = f"=F{count}*E{count}"

        simpleRow = [
            code,
            name,
            stock,
            cja,
            final,
            costCja,
            monto
        ]

        if includeProvider:
            simpleRow.append(provider)

        result.append(simpleRow)

    return result


# ============================================================
# FORMATO VISUAL DE EXCEL
# ============================================================

def applyExcelFormatting(filePath):

    wb = load_workbook(filePath)

    headerFill = PatternFill(
        fill_type="solid",
        fgColor="17365D"
    )

    headerFont = Font(
        name="Arial",
        size=10,
        bold=True,
        color="FFFFFF"
    )

    bodyFont = Font(
        name="Arial",
        size=10,
        color="222222"
    )

    thinGray = Side(
        style="thin",
        color="D9E2F3"
    )

    for ws in wb.worksheets:

        ws.freeze_panes = "A2"

        ws.auto_filter.ref = ws.dimensions

        ws.sheet_view.showGridLines = False

        # Encabezados
        for cell in ws[1]:

            cell.fill = headerFill
            cell.font = headerFont

            cell.alignment = Alignment(
                horizontal="center",
                vertical="center",
                wrap_text=True
            )

            cell.border = Border(
                bottom=Side(
                    style="medium",
                    color="4472C4"
                )
            )

        ws.row_dimensions[1].height = 32

        headers = {
            str(cell.value): cell.column
            for cell in ws[1]
        }

        # Anchos generales
        for column in ws.columns:

            letter = column[0].column_letter
            header = str(column[0].value or "")

            maxLength = len(header)

            for cell in column[1:]:

                if cell.value is not None:

                    lines = str(cell.value).split("\n")

                    maxLength = max(
                        maxLength,
                        max(len(line) for line in lines)
                    )

            width = min(max(maxLength + 3, 12), 35)

            if header == "NOMBRE":
                width = 52

            elif header == "PRVDOR":
                width = 30

            elif header in ("COD", "PA"):
                width = max(width, 15)

            elif header in ("MONTO", "COSTOCJA", "COSTO", "PRECIO"):
                width = 16

            ws.column_dimensions[letter].width = width

        # Formato de celdas
        for row in ws.iter_rows(min_row=2):

            ws.row_dimensions[row[0].row].height = 30

            for cell in row:

                cell.font = bodyFont

                cell.alignment = Alignment(
                    vertical="center",
                    horizontal="left" if cell.column == headers.get("NOMBRE") else "center",
                    wrap_text=True
                )

                cell.border = Border(
                    bottom=thinGray
                )

            # Formato de valores monetarios
            for columnName in [
                "COSTO", "PRECIO", "COSTOCJA", "MONTO"
            ]:

                columnIndex = headers.get(columnName)

                if columnIndex:

                    ws.cell(
                        row=row[0].row,
                        column=columnIndex
                    ).number_format = '#,##0.00'

            # Formato numérico
            for columnName in [
                "STOCK", "VENTAS", "BLI", "CJA", "FINAL"
            ]:

                columnIndex = headers.get(columnName)

                if columnIndex:

                    ws.cell(
                        row=row[0].row,
                        column=columnIndex
                    ).number_format = '#,##0.##'

    wb.save(filePath)


# ============================================================
# EXPORTACION DE EXCEL
# ============================================================

def writeExcelSheet(writer, data, columns, sheetName):

    df = pd.DataFrame(
        data,
        columns=columns
    )

    df.to_excel(
        writer,
        sheet_name=sheetName,
        index=False
    )


def createOutputDirectory():

    output = Path("./out")

    output.mkdir(
        parents=True,
        exist_ok=True
    )

    return output


def exportIndividualProvider(prodDict, providerName):

    print("\nGenerando pedido: " + providerName)

    if not prodDict:

        print("No se encontraron productos para " + providerName)
        return

    providers = []

    data = createDataList(
        prodDict,
        providers
    )

    if simple_mode:

        data = createSimpleRows(
            data,
            includeProvider=False
        )

        columns = SIMPLE_COLUMNS

    else:

        columns = FULL_COLUMNS

    output = createOutputDirectory()

    now = datetime.now().strftime("%Y%m%d_%H%M")

    filename = (
        str(business_)
        + "_Pedido_"
        + safeFileName(providerName)
        + "_"
        + now
        + ".xlsx"
    )

    fullpath = output / filename

    with pd.ExcelWriter(fullpath, engine="openpyxl") as writer:

        writeExcelSheet(
            writer,
            data,
            columns,
            "Productos"
        )

    applyExcelFormatting(fullpath)

    print("\nExcel generado correctamente:")
    print(fullpath)


def exportAllProviders(prodDict, forceFull=False):

    print("\nGenerando Excel de todos los proveedores...")

    providers = []

    # Se calcula con todos los productos.
    data = createDataList(
        prodDict,
        providers
    )

    useSimple = simple_mode and not forceFull

    if useSimple:

        data = createSimpleRows(
            data,
            includeProvider=True
        )

        columns = SIMPLE_ALL_COLUMNS

    else:

        columns = FULL_COLUMNS

    groups = getActualProviderGroups(prodDict)

    output = createOutputDirectory()

    now = datetime.now().strftime("%Y%m%d_%H%M")

    filename = (
        str(business_)
        + "_Pedido_TODOS_"
        + now
        + ".xlsx"
    )

    fullpath = output / filename

    usedSheetNames = {"PRODUCTOS"}

    with pd.ExcelWriter(fullpath, engine="openpyxl") as writer:

        # Hoja general
        writeExcelSheet(
            writer,
            data,
            columns,
            "Productos"
        )

        # Una hoja por cada proveedor real de Susii.
        for providerName, providerProducts in groups.items():

            sheetName = safeSheetName(
                "Lista_" + providerName
            )

            baseName = sheetName
            suffix = 1

            while sheetName.upper() in usedSheetNames:

                suffix += 1

                sheetName = safeSheetName(
                    baseName[:26] + "_" + str(suffix)
                )

            usedSheetNames.add(sheetName.upper())

            providerList = []

            providerData = createDataList(
                providerProducts,
                providerList
            )

            if useSimple:

                providerData = createSimpleRows(
                    providerData,
                    includeProvider=True
                )

            writeExcelSheet(
                writer,
                providerData,
                columns,
                sheetName
            )

    applyExcelFormatting(fullpath)

    print("\nExcel generado correctamente:")
    print(fullpath)


# ============================================================
# CARGA Y PREPARACION GENERAL
# ============================================================

def prepareProducts():

    prodDict, packDict = loadProductAndPackageData()

    # Aumentar ventas por paquetes.
    increaseSoldUnitsByPackages(
        prodDict,
        packDict
    )

    # Combinar productos.
    prodDict = QantuProductMerger.combineProducts(
        prodDict
    )

    return prodDict


# ============================================================
# OPCION 1: REVISION GENERAL DE VENTAS
# ============================================================

def runSalesReview():

    global stock_0

    print("\n==============================================")
    print("         REVISION GENERAL DE VENTAS")
    print("==============================================")

    print("Descargando productos...")

    stock_0 = True

    try:

        prodDict = prepareProducts()

        # Siempre genera el formato completo.
        # No depende de SIMPLE_MODE.
        exportAllProviders(
            prodDict,
            forceFull=True
        )

    finally:

        # Restablecer el comportamiento normal.
        stock_0 = False

    print("\nRevision general finalizada.")


# ============================================================
# OPCION 2: PEDIDOS POR PROVEEDOR
# ============================================================

def showProviderMenu():

    filters = getProviderFilters()

    providerNames = list(filters.keys())

    print("\n==============================================")
    print("             PEDIDOS POR PROVEEDOR")
    print("==============================================")

    for index, name in enumerate(providerNames, start=1):

        aliases = filters.get(name, [])

        print(
            f" {index}. {name} "
            f"({len(aliases)} nombres configurados)"
        )

    print(f" {len(providerNames) + 1}. TODOS LOS PROVEEDORES")
    print(" 0. Regresar al menu principal")

    print("----------------------------------------------")


def runProviderOrders():

    providerFilters = getProviderFilters()

    providerNames = list(providerFilters.keys())

    if not providerNames:

        print("No hay proveedores configurados en cfg.json.")
        return

    while True:

        showProviderMenu()

        selection = input(
            "Seleccione uno o varios proveedores: "
        ).strip()

        if selection == "0":
            return

        try:

            selected = [
                int(value.strip())
                for value in selection.split(",")
            ]

        except ValueError:

            print("Seleccion invalida.")
            continue

        if len(set(selected)) != len(selected):

            print("No repita opciones.")
            continue

        allOption = len(providerNames) + 1

        if any(
            value < 0 or value > allOption
            for value in selected
        ):

            print("Una o varias opciones no existen.")
            continue

        if allOption in selected:

            if len(selected) != 1:

                print(
                    "TODOS LOS PROVEEDORES debe seleccionarse solo."
                )

                continue

            prodDict = prepareProducts()

            exportAllProviders(prodDict)

            return

        if not selected:
            continue

        # Descargar una sola vez para todos los proveedores elegidos.
        prodDict = prepareProducts()

        for option in selected:

            providerName = providerNames[option - 1]

            aliases = providerFilters.get(
                providerName,
                []
            )

            if not aliases:

                print(
                    f"\nATENCION: {providerName} "
                    "no tiene nombres configurados en cfg.json."
                )

                continue

            filteredProducts = filterProductsByProvider(
                prodDict,
                providerName
            )

            if not filteredProducts:

                print(
                    f"\nNo se encontraron productos "
                    f"para {providerName}."
                )

                continue

            exportIndividualProvider(
                filteredProducts,
                providerName
            )

        return


# ============================================================
# CONFIGURACION DEL MENU
# ============================================================

def changeNbrDays():

    global NBR_DAYS

    print("\n==============================================")
    print("             CAMBIAR NBR_DAYS")
    print("==============================================")
    print(f"Valor actual: {NBR_DAYS}")
    try:
        newValue = int(input("Nuevo numero de dias: "))
        if newValue <= 0:
            print("Ingrese un valor mayor que cero.")
            return
        NBR_DAYS = newValue
        QantuConfiguration.NBR_DAYS = newValue
        saveCfg()
        print("NBR_DAYS actualizado correctamente.")
    except ValueError:
        print("Ingrese un numero entero valido.")


def toggleSimpleMode():

    global simple_mode

    simple_mode = not simple_mode

    saveCfg()

    status = "ACTIVADO" if simple_mode else "DESACTIVADO"

    print(
        f"\nSIMPLE_MODE ahora esta {status}."
    )


def showConfiguration():

    print("\n==============================================")
    print("           CONFIGURACION ACTUAL")
    print("==============================================")

    print(f"BUSINESS_ID : {business_}")
    print(f"NBR_DAYS    : {NBR_DAYS}")
    print(f"ZERO_STOCK  : False (FIJO)")
    print(
        f"SIMPLE_MODE : "
        f"{'True' if simple_mode else 'False'}"
    )

    print("\nPROVEEDORES CONFIGURADOS:")

    for name, aliases in getProviderFilters().items():

        print(f"\n{name}")

        if aliases:

            for alias in aliases:
                print(f"  - {alias}")

        else:

            print("  (Sin nombres configurados)")

    print("\nCFG:", CFG_PATH)


# ============================================================
# MENU PRINCIPAL
# ============================================================

def showMainMenu():

    print("\n")
    print("=" * 52)
    print("       QANTUFARMA - GENERADOR DE PEDIDOS V2")
    print("=" * 52)

    print("\nCONFIGURACION ACTUAL")

    print(f" NBR_DAYS    : {NBR_DAYS}")
    print(" ZERO_STOCK  : False (FIJO)")

    print(
        f" SIMPLE_MODE : "
        f"{'True' if simple_mode else 'False'}"
    )

    print("\n" + "=" * 52)
    print("                 MENU PRINCIPAL")
    print("=" * 52)

    print("\n 1. Revision general de ventas (STOCK = 0)")
    print(" 2. Generar pedido por proveedor")
    print(" 3. Cambiar NBR_DAYS")
    print(" 4. Activar / Desactivar SIMPLE_MODE")
    print(" 5. Mostrar configuracion")
    print(" 0. Salir")

    print("\n" + "=" * 52)


def main():

    while True:

        showMainMenu()

        option = input(
            "\nSeleccione una opcion: "
        ).strip()

        if option == "1":

            runSalesReview()

        elif option == "2":

            runProviderOrders()

        elif option == "3":

            changeNbrDays()

        elif option == "4":

            toggleSimpleMode()

        elif option == "5":

            showConfiguration()

        elif option == "0":

            print("\nSaliendo del generador de pedidos.")

            break

        else:

            print("\nOpcion no valida. Intente nuevamente.")


# ============================================================
# EJECUCION
# ============================================================

if __name__ == "__main__":

    main()
