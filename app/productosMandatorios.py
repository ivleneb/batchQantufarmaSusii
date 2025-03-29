import sys, os
# print the original sys.path
#print('Original sys.path:', sys.path)
# append a new directory to sys.path
sys.path.append(r'F:\proyectos\botica\qantufarma')
# print the updated sys.path
#print('Updated sys.path:', sys.path)
# now you can import your module
#import your_module


import pandas
from datetime import datetime
from lib.libclass import *
from lib.ReportDownloader import *
#import sys

# adding Folder_2 to the system path
#sys.path.insert(0, 'F:\proyectos\botica\library')

def getProduct(row):
    return QantuMedicine(row['CÓDIGO'], row['NOMBRE'], row['CANTIDAD'], row['disable (EXTRA)'], minStock=row['STOCK MÍNIMO'])

def createDatalist(prodDict):
    data = []
    for key, prod in prodDict.items():
        diff = prod.getMinStock()-prod.getStock()
        data.append([prod.getCode(), prod.getName(), prod.getMinStock(), prod.getStock(), 2*diff ])
    return data

# download products
repHeaders = ["CÓDIGO", "NOMBRE", "STOCK MÍNIMO", "CANTIDAD", "disable (EXTRA)"]
rd = ReportDownloader("Exportar productos.xlsx", "export_products",
                      repHeaders, '2024-02-04',
                      '2024-02-05', "MEDICAMENTOS")
file1 = rd.execute()
if file1 == "":
    sys.exit("Can't dowloand file.")

med_df = pandas.read_excel(file1, skiprows=4)
print("REG SIZE (prod sales):"+str(len(med_df)))

prodDict = {}
# selecciona medicmantos con stock minimo
for index, row in med_df.iterrows():
    # only add sales that are products
    prod = getProduct(row)
    if prod is not None and not prod.isDisable() and not prod.isNoUsar() and prod.getMinStock()!=0:
        # add product to data dict
        if prod.getCode() in prodDict:
            raise Exception("Key must be unique")
        prodDict[prod.getCode()]=prod
        #print("\nADDED!\n")
        #print(row)

# une los stocks de medicamentos con mismo cc, ff, y form
# Combine medicine items with same form and concentration
print("Second product filter")
prodDictFilter = {}
for code in list(prodDict):
    if not code in prodDict:
        continue
    
    prod = prodDict[code]
    
    formu = prod.getFormula()
    if formu == "":
        print("WARNING: Invalid formula for "+prod.getName())
        continue

    cc = prod.getConcentration()
    if cc == "":
        print("Invalid cc")
        continue

    ff  = prod.getFF()
    if ff == "":
        print("Invalid ff")
        continue

    for code2 in list(prodDict):
        if code == code2:
            continue
        if not code in prodDict:
            continue
        prod2 = prodDict[code2]
        if prod2.getCategory() is not 'MEDICAMENTOS':
            continue
        
        if formu == prod2.getFormula():
            if cc == prod2.getConcentration():
                if ff == prod2.getFF():
                    prod.merge(prod2)
                    del prodDict[code2]


# compara stock minimo con stock actual, indicar cantidad a comprar

dataMeds = createDatalist(prodDict)
cols = ['COD', 'NOMBRE', 'STOCK MIN', 'STOCK', 'COMPRAR']
outMed_df = pandas.DataFrame(dataMeds, columns = cols)
#outOther_df = pandas.DataFrame(dataOther, columns = cols)

now = datetime.now().strftime("%Y%m%d")
excel_name = 'ListaMandatorios_'+now+'.xlsx'
#outMed_df.to_excel(excel_name, sheet_name = 'Medicamentos', index=False)
#outOther_df.to_excel(excel_name, sheet_name = 'Otros', index=False)

with pandas.ExcelWriter(excel_name) as excel_writer:
    outMed_df.to_excel(excel_writer, index=False)
