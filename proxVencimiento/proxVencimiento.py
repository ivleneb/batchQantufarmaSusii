import sys
sys.path.append(r'../')
from lib.QantuMedicine import QantuMedicine
from lib.QantuGalenico import QantuGalenico
from lib.QantuDevice import QantuDevice
from lib.QantuGeneral import QantuGeneral
#from lib.QantuPackage import QantuPackage
#from lib.QantuProduct import QantuProduct
from lib.ReportDownloader import ReportDownloader
import pandas
from datetime import datetime
import json

# Read JSON file
with open('../lib/cfg.json', 'r', encoding='utf-8') as file:
    dataCfg = json.load(file)
    business_ = dataCfg["businessId"]

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
        if isinstance(row['fecha_vto (EXTRA)'], str):
            prod.setFechaVto(row['fecha_vto (EXTRA)'])
        elif prod.getStock()!=0:
            print("Invalid fecha_vto["+str(row['fecha_vto (EXTRA)'])+"] for "+prod.getName())
            return None
        else:
            return None
        return prod
    elif len(sub_df)==0:
        print("Product not found")
        return None
    else:
        raise Exception("Code with multiple products.")

def createDataList(prodDict):
    data = []
    count = 0

    for key, prod in prodDict.items():
        count = count + 1

        if prod.getRemainingDays()<=60 and prod.getStock()!=0:
            data.append( [prod.getCode(), prod.getName(), prod.getCategory(), prod.getLastCost(),
                      prod.getPrice(), prod.getStock(), prod.getCreatedAt(), prod.getFechaVto()])
    return data


def run():
    prodDict = {}
    today = datetime.now().strftime("%Y-%m-%d")

    # download product data
    repHeaders = ["CÓDIGO", "NOMBRE", "STOCK MÍNIMO", "CANTIDAD", "disable (EXTRA)",
                  "creado (EXTRA)", "fecha_vto (EXTRA)", "CATEGORÍA", "PRECIO DE VENTA", "PRECIO DE COMPRA",
                  "generico (EXTRA)"]
    rd = ReportDownloader("Exportar productos.xlsx", "export_products",
                          repHeaders, '2024-02-12',
                          today)
    file_prod = rd.execute()
    if file_prod == "":
        sys.exit("Can't dowloand file[Exportar productos.xlsx]")

    prod_df = pandas.read_excel(file_prod, skiprows=4)
    print("REG SIZE (prod):"+str(len(prod_df)))

    # Load products
    for index, row in prod_df.iterrows():
        # only add sales that are products
        prod = getProduct(prod_df, row['CÓDIGO'])
        if prod is not None:
            # add product to data dict
            if prod.getCode() in prodDict:
                raise Exception("Key must be unique")
            prodDict[prod.getCode()]=prod
            #if prod.getCategory()=='MEDICAMENTOS':
            #    print(prod.getName())
            #    print(prod.isGenerico())


    medsDict = {}
    otherDict = {}
    for key, prod in prodDict.items():
        if prod.getCategory()=='MEDICAMENTOS':
            medsDict[key]=prod
        else:
            otherDict[key]=prod

    dataMeds = createDataList(medsDict)
    dataOther = createDataList(otherDict)

    cols = ['COD', 'NOMBRE', 'CATEGORIA', 'COSTO', 'PRECIO', 'STOCK', 
            'CREADO', 'FECHA VTO' ]

    outMed_df = pandas.DataFrame(dataMeds, columns = cols)
    outOther_df = pandas.DataFrame(dataOther, columns = cols)

    now = datetime.now().strftime("%Y%m%d")
    excel_name = str(business_)+'_ProxVto_'+now+'.xlsx'

    with pandas.ExcelWriter(excel_name) as excel_writer:
        outMed_df.to_excel(excel_writer, sheet_name='Medicamentos', index=False)
        outOther_df.to_excel(excel_writer, sheet_name='Otros', index=False)

run()