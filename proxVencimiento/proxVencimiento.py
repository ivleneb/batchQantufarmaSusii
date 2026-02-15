import sys
sys.path.append(r'../')
from lib.QantuProduct import QantuProduct
from lib.QantuConfiguration import QantuConfiguration
from lib.SusiiProductLoader import SusiiProductLoader
import pandas
from datetime import datetime

config = QantuConfiguration()
business_ = config.business_

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
    loader = SusiiProductLoader(business_)

    # load products from q1
    prodDict:dict[str, QantuProduct] = loader.downloadProducts()
    if not prodDict:
        print("Fail to downloadProducts.")
        sys.exit(2)

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