import sys
sys.path.append(r'../')
#from lib.libclass import *
from lib.ReportDownloader import ReportDownloader
import pandas
from datetime import datetime
#from datetime import timedelta
#import re
#import math
import json

# Read JSON file
with open('../lib/cfg.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
    business_ = data["businessId"]

now = datetime.now().strftime("%Y-%m-%d")
# download product data
repHeaders = ["CÓDIGO", "NOMBRE", "PRECIO DE VENTA", "num_regsan (EXTRA)",
              "lab (EXTRA)", "disable (EXTRA)"]

# repHeaders = ["CÓDIGO", "NOMBRE", "STOCK MÍNIMO", "CANTIDAD", "generico (EXTRA)", "disable (EXTRA)",
#              "creado (EXTRA)", "lab (EXTRA)", "units_caja (EXTRA)", "units_blister (EXTRA)", "CATEGORÍA",
#              "PRECIO DE VENTA", "PRECIO DE COMPRA"]
#
rd = ReportDownloader("Exportar productos.xlsx", "export_products",
                      repHeaders, '2024-02-12',
                      now)
file_prod = rd.execute()
if file_prod == "":
    sys.exit("Can't dowloand file[Exportar productos.xlsx]")
catQantu_df = pandas.read_excel(file_prod, skiprows=4)
catDiris_df = pandas.read_excel('catalogoproductos_2026-01-27T21_39_02-05_00.xlsx', sheet_name='Catálogo', skiprows=6)



print(catQantu_df)
# print whole sheet data
count = 0
data = []
added = []
for index, row in catQantu_df.iterrows():
    if row['disable (EXTRA)']==1:
        continue
    found = catDiris_df.loc[catDiris_df['Num_RegSan'] == row['num_regsan (EXTRA)']]
    for i, rec in found.iterrows():
        count = count + 1
        unitPrice = row['PRECIO DE VENTA']
        fracUnitPrice = unitPrice*rec['Fracción']
        if rec['Cod_Prod'] in added:
            print("Codigo de producto ya esta en uso")
            continue
        #print(rec['Cod_Prod'], ',', rec['Nom_Prod'], ',', rec['Concent'], ',', rec['Fracciones'], ',', unitPrice, unitPrice*rec['Fracciones']);
        data.append(['0112946', rec['Cod_Prod'], '%.2f' % fracUnitPrice, '%.2f' % unitPrice])
        added.append(rec['Cod_Prod'])

print("COUNT: "+str(count))
out_df = pandas.DataFrame(data, columns =['CodEstab', 'CodProd', 'Precio 1', 'Precio 2'])
cMonth = datetime.now().strftime("%m")
cYear = datetime.now().strftime("%y")
out_df.to_csv('20610850040_0112946_'+cMonth+'_'+cYear+'_CARGA ARCHIVO.csv', index=False, sep=';')