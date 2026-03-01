import sys
sys.path.append(r'../')
from lib.ReportDownloader import ReportDownloader
import pandas
from datetime import datetime
import json
import os

# Read JSON file
with open('../lib/cfg.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
    business_ = data["businessId"]

def loadDirisFile():
    ruta = './catalogo diris'
    files = [f for f in os.listdir(ruta) if os.path.isfile(os.path.join(ruta, f))]
    count = 1
    for file in files:
        print(str(count)+":"+file)
        count+=1
    nbrCatalogs = len(files)
    if nbrCatalogs>1:
        while True:
            try:
                val = int(input("Elige el número del catálogo de diris a usar: "))
                if val>nbrCatalogs or val<=0:
                    print("Número invalido.")
                else:
                    print("Catalogo seleccionado: "+files[val-1])
                    return ruta+"/"+files[val-1]
            except ValueError:
                print("Ingresaste una letra o texto. Volver a ingresar.")
    else:
        return ruta+"/"+files[0]

def run():

    code = ''
    if business_ == 5053:
        code = '0112946'
    elif business_ == 8132:
        code = '0124186'

    now = datetime.now().strftime("%Y-%m-%d")
    # download product data
    repHeaders = ["CÓDIGO", "NOMBRE", "PRECIO DE VENTA", "num_regsan (EXTRA)",
                  "lab (EXTRA)", "disable (EXTRA)"]

    rd = ReportDownloader("Exportar productos.xlsx", "export_products",
                          repHeaders, '2024-02-12',
                          now)
    file_prod = rd.execute()
    if file_prod == "":
        sys.exit("Can't dowloand file[Exportar productos.xlsx]")
    catQantu_df = pandas.read_excel(file_prod, skiprows=4)
    
    
    catalogFile = loadDirisFile()
    if catalogFile is None or len(catalogFile)==0:
        print("Invalid catalog file.")
        sys.exit(1)
    catDiris_df = pandas.read_excel(catalogFile, sheet_name='Catálogo', skiprows=6)

    #print(catQantu_df)
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
            data.append([code, rec['Cod_Prod'], '%.2f' % fracUnitPrice, '%.2f' % unitPrice])
            added.append(rec['Cod_Prod'])

    print("COUNT: "+str(count))
    out_df = pandas.DataFrame(data, columns =['CodEstab', 'CodProd', 'Precio 1', 'Precio 2'])
    cMonth = datetime.now().strftime("%m")
    cYear = datetime.now().strftime("%y")

    filename = '20610850040_'+code+'_'+cMonth+'_'+cYear+'_CARGA ARCHIVO.csv'
    out_path = './out'
    fullpath = out_path+'/'+filename
    out_df.to_csv(fullpath, index=False, sep=';')

run()